"""The match-score formula, kept as separate sub-scores so the explanation engine can point
to exactly why a job scored the way it did:

    match = w_semantic * semantic_similarity
          + w_skills * skill_overlap
          + w_location * location_fit
          + w_salary * salary_fit
          + w_experience * experience_fit
          + w_job_type * job_type_fit
          + w_recency * recency_score

Weights come from scoring_config.py (versioned, for ablation studies)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.job import Job
from app.models.user import UserProfile
from app.processing.skills import _resolve_alias
from app.services.scoring_config import ScoringWeights, load_weights


EXPERIENCE_ORDER = ["intern", "junior", "entry", "mid", "senior", "lead", "principal", "director"]

# Simple currency conversion rates (base: USD)
CURRENCY_RATES = {
    "USD": 1.0,
    "GBP": 1.27,
    "EUR": 1.09,
    "CAD": 0.74,
    "AUD": 0.66,
    "INR": 0.012,
    "SGD": 0.74,
    "CHF": 1.13,
    "JPY": 0.0067,
    "NZD": 0.61,
}


@dataclass
class MatchBreakdown:
    """Transparent scoring breakdown - this feeds directly into the explanation engine."""
    semantic_similarity: float = 0.0
    skill_overlap: float = 0.0
    location_fit: float = 0.0
    salary_fit: float = 0.0
    experience_fit: float = 0.0
    job_type_fit: float = 0.0
    recency_score: float = 0.0

    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)

    overall_score: float = 0.0  # 0.0 - 1.0
    match_percentage: float = 0.0  # 0 - 100

    # Hard constraint filters (applied before scoring)
    passes_hard_filters: bool = True
    hard_filter_failures: list[str] = field(default_factory=list)
    weight_version: str = "v2.0"


def compute_match_score(
    profile: UserProfile,
    job: Job,
    job_skills: list[str],
    semantic_similarity: float,
    preferred_job_types: list[str] | None = None,
    weight_version: str | None = None,
    hard_constraints: dict | None = None,
    weights: ScoringWeights | None = None,
) -> MatchBreakdown:
    """Compute the full match score for a profile/job pair.

    hard_constraints, if given, must ALL pass or the job scores 0 - expected keys:
    "locations" (list[str]), "remote_only" (bool), "min_salary" (float), "job_types" (list[str]).
    
    weights, if given, overrides weight_version for scoring.
    """
    if weights is None:
        weights = load_weights(weight_version)
    breakdown = MatchBreakdown(
        semantic_similarity=semantic_similarity,
        weight_version=weights.version,
    )

    # ── Hard constraint filtering ──
    if hard_constraints:
        failures = _check_hard_constraints(job, hard_constraints)
        breakdown.hard_filter_failures = failures
        if failures:
            breakdown.passes_hard_filters = False
            breakdown.overall_score = 0.0
            breakdown.match_percentage = 0.0
            return breakdown

    # ── Soft scoring ──
    breakdown.skill_overlap, breakdown.matching_skills, breakdown.missing_skills = \
        _score_skills(profile.skills or [], job_skills)

    breakdown.location_fit = _score_location(
        profile.preferred_locations or [],
        job.location_city, job.location_country, job.remote,
        getattr(job, 'workplace_type', None),
    )

    breakdown.salary_fit = _score_salary(
        profile.min_salary, profile.salary_currency,
        job.salary_min, job.salary_max, job.salary_currency,
    )

    breakdown.experience_fit = _score_experience(profile.experience_level, job.experience_level)

    breakdown.job_type_fit = _score_job_type(
        preferred_job_types or profile.preferred_job_types or [],
        job.job_type,
    )

    breakdown.recency_score = _score_recency(job.posted_at)

    # Weighted total using configurable weights
    breakdown.overall_score = (
        weights.semantic * breakdown.semantic_similarity +
        weights.skills * breakdown.skill_overlap +
        weights.location * breakdown.location_fit +
        weights.salary * breakdown.salary_fit +
        weights.experience * breakdown.experience_fit +
        weights.job_type * breakdown.job_type_fit +
        weights.recency * breakdown.recency_score
    )
    breakdown.match_percentage = round(breakdown.overall_score * 100, 1)

    return breakdown


def _check_hard_constraints(job: Job, constraints: dict) -> list[str]:
    """Check if a job passes all hard constraints.

    Returns a list of failure reasons (empty = all passed).
    """
    failures = []

    # Location constraint
    required_locations = constraints.get("locations", [])
    if required_locations:
        job_location = f"{job.location_city or ''} {job.location_country or ''}".lower()
        location_match = any(
            loc.lower() in job_location
            for loc in required_locations if loc
        )
        if not location_match and not job.remote:
            failures.append(f"location_not_in_{required_locations}")

    # Remote-only constraint
    if constraints.get("remote_only") and not job.remote:
        failures.append("not_remote")

    # Minimum salary constraint
    min_salary = constraints.get("min_salary")
    if min_salary is not None:
        job_max = job.salary_max or job.salary_min
        if job_max is not None:
            # Convert to common currency (USD)
            job_max_usd = job_max * CURRENCY_RATES.get(
                (job.salary_currency or "USD").upper(), 1.0
            )
            min_salary_usd = min_salary * CURRENCY_RATES.get(
                (constraints.get("salary_currency") or "USD").upper(), 1.0
            )
            if job_max_usd < min_salary_usd:
                failures.append("salary_below_minimum")

    # Job type constraint
    required_types = constraints.get("job_types", [])
    if required_types and job.job_type:
        job_type_lower = job.job_type.lower()
        if not any(t.lower() == job_type_lower for t in required_types):
            failures.append(f"job_type_not_in_{required_types}")

    return failures


def _score_skills(
    user_skills: list[str],
    job_skills: list[str],
    job_skill_classifications: dict[str, str] | None = None,
) -> tuple[float, list[str], list[str]]:
    """Bidirectional skill overlap with classification-weighted scoring.

    Balances coverage (what % of job requirements the user meets) with
    alignment (what % of user skills are relevant to the job).

    Both user and job skills are alias-resolved before comparison so that
    e.g. user's "reactjs" matches job's "react", user's "ml" matches "machine learning".

    job_skill_classifications, if provided, maps canonical skill name to one of
    "required", "preferred", "desirable", "mentioned". Required skills carry
    more weight in the coverage calculation.
    """
    if not job_skills:
        return 0.5, [], []

    user_set = {_resolve_alias(s) for s in user_skills}
    job_set = {_resolve_alias(s) for s in job_skills}

    matching = sorted(user_set & job_set)
    missing = sorted(job_set - user_set)

    if job_skill_classifications:
        # Weighted coverage: required=1.0, preferred=0.7, desirable=0.5, mentioned=0.3
        class_weights = {
            "required": 1.0, "preferred": 0.7,
            "desirable": 0.5, "mentioned": 0.3,
        }
        weighted_total = 0.0
        weighted_met = 0.0
        for skill in job_set:
            w = class_weights.get(
                job_skill_classifications.get(skill, "required"), 1.0
            )
            weighted_total += w
            if skill in user_set:
                weighted_met += w

        coverage = weighted_met / weighted_total if weighted_total else 0.0
    else:
        coverage = len(matching) / len(job_set) if job_set else 0.0

    # Alignment: what fraction of user's listed skills are relevant
    alignment = len(matching) / len(user_set) if user_set else 0.0

    score = 0.6 * coverage + 0.4 * alignment

    # Bonus: if user covers ALL required skills, give a boost
    if job_skill_classifications:
        required_skills = {
            s for s, c in job_skill_classifications.items() if c == "required"
        }
        required_resolved = {_resolve_alias(s) for s in required_skills}
        if required_resolved and required_resolved.issubset(user_set):
            score = min(score + 0.1, 1.0)

    return round(score, 3), matching, missing


def _score_location(
    preferred_locations: list[str],
    job_city: str | None,
    job_country: str | None,
    job_remote: bool,
    job_workplace_type: str | None = None,
) -> float:
    """Location fit with tiered scoring for proximity and remote flexibility.

    Scoring tiers:
      1.0  – remote job, or city-level match
      0.85 – hybrid with city match (flexible commute)
      0.7  – same country / region match
      0.5  – no preferences set, or remote/hybrid listed as preference
      0.25 – country-level partial match
      0.0  – no match
    """
    if job_remote:
        return 1.0

    if not preferred_locations:
        return 0.5

    job_location_text = f"{job_city or ''} {job_country or ''}".lower()
    workplace_lower = (job_workplace_type or "").lower()

    # Exact city-level match
    for pref in preferred_locations:
        pref_lower = pref.lower().strip()
        if pref_lower and pref_lower in job_location_text:
            if workplace_lower == "hybrid":
                return 0.85
            return 1.0

    # Check for remote/hybrid preference keywords in user's preferences
    remote_prefs = {"remote", "work from home", "wfh", "anywhere", "hybrid"}
    for pref in preferred_locations:
        if pref.lower().strip() in remote_prefs:
            if job_remote or workplace_lower in ("hybrid", "remote"):
                return 0.9
            return 0.3

    # Country / region match
    if job_country:
        job_country_lower = job_country.lower()
        for pref in preferred_locations:
            pref_lower = pref.lower().strip()
            if not pref_lower:
                continue
            # Direct country name match
            if job_country_lower == pref_lower:
                return 0.7
            # Partial containment (e.g. "london" in "united kingdom" check)
            if pref_lower in job_country_lower or job_country_lower in pref_lower:
                return 0.6
            # Region-level match (e.g. "europe" matching "Germany")
            if _is_region_match(pref_lower, job_country_lower):
                return 0.55

    return 0.0


def _is_region_match(pref: str, country: str) -> bool:
    """Check if a preference string is a broad region matching a country."""
    REGIONS = {
        "europe": {"uk", "united kingdom", "germany", "france", "spain", "netherlands",
                    "ireland", "sweden", "denmark", "finland", "norway", "italy",
                    "portugal", "belgium", "austria", "switzerland", "poland", "czech"},
        "north america": {"united states", "usa", "canada", "mexico"},
        "asia pacific": {"australia", "new zealand", "singapore", "japan", "india"},
        "uk": {"united kingdom", "england", "scotland", "wales"},
    }
    for region, countries in REGIONS.items():
        if pref == region and country in countries:
            return True
    return False


def _convert_to_usd(amount: float, currency: str | None) -> float:
    """Convert an amount from the given currency to USD."""
    if not currency:
        return amount
    rate = CURRENCY_RATES.get(currency.upper(), 1.0)
    return amount * rate


def _score_salary(
    user_min_salary: float | None,
    user_currency: str | None,
    job_salary_min: float | None,
    job_salary_max: float | None,
    job_currency: str | None,
) -> float:
    """Salary fit: 1.0 if job meets/exceeds user's minimum, scaled otherwise."""
    if user_min_salary is None:
        return 0.5

    job_ceiling = job_salary_max or job_salary_min
    if job_ceiling is None:
        return 0.5

    user_min_usd = _convert_to_usd(user_min_salary, user_currency)
    job_ceiling_usd = _convert_to_usd(job_ceiling, job_currency)

    if job_ceiling_usd >= user_min_usd:
        return 1.0

    ratio = job_ceiling_usd / user_min_usd
    if ratio >= 0.8:
        return round(0.5 + (ratio - 0.8) * 2.5, 3)

    return round(max(ratio * 0.5, 0.0), 3)


def _score_experience(user_level: str | None, job_level: str | None) -> float:
    """Experience fit: 1.0 exact match, scaled by distance in seniority order."""
    if not user_level or not job_level:
        return 0.5

    user_lower = user_level.lower().strip()
    job_lower = job_level.lower().strip()

    if user_lower == job_lower:
        return 1.0

    try:
        user_idx = EXPERIENCE_ORDER.index(user_lower)
        job_idx = EXPERIENCE_ORDER.index(job_lower)
        distance = abs(user_idx - job_idx)
        return round(max(1.0 - distance * 0.25, 0.0), 3)
    except ValueError:
        return 0.5


def _score_job_type(preferred_types: list[str], job_type: str | None) -> float:
    """Job type fit: 1.0 if matches preference, 0.5 if no preference or unknown."""
    if not preferred_types or not job_type:
        return 0.5

    job_type_lower = job_type.lower().strip()
    preferred_lower = {t.lower().strip() for t in preferred_types}

    type_mapping = {
        "full-time": "full-time", "fulltime": "full-time", "full time": "full-time",
        "part-time": "part-time", "parttime": "part-time", "part time": "part-time",
        "contract": "contract",
        "temporary": "temporary", "temp": "temporary",
        "internship": "internship", "intern": "internship",
    }

    normalized_job_type = type_mapping.get(job_type_lower, job_type_lower)

    for pref in preferred_lower:
        normalized_pref = type_mapping.get(pref, pref)
        if normalized_pref == normalized_job_type:
            return 1.0

    return 0.0


def _score_recency(posted_at: datetime | None) -> float:
    """Recency score: 1.0 for fresh jobs, decaying over time."""
    if posted_at is None:
        return 0.5

    now = datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    age_days = (now - posted_at).days

    if age_days <= 7:
        return 1.0
    if age_days <= 14:
        return 0.9
    if age_days <= 30:
        return 0.8
    if age_days <= 45:
        return 0.7
    if age_days <= 60:
        return 0.6
    if age_days <= 90:
        return 0.4
    if age_days <= 180:
        return 0.2
    return 0.1
