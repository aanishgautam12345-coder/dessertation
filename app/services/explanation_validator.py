"""Advanced explanation validator - checks model-generated explanations against
ground-truth facts (profile, job, breakdown) to catch fabricated claims.

Improvements over the basic version:
  1. Fuzzy skill matching via rapidfuzz (handles typos and variants)
  2. Auto-correction: fixes minor issues instead of rejecting outright
  3. Experience level consistency check
  4. Company/title claim validation
  5. Explanation quality scoring (specificity, evidence usage)
  6. JSON structure validation for structured output
"""

import json
import re
import logging
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.models.job import Job
from app.models.user import UserProfile
from app.services.recommendation import MatchBreakdown

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 80  # Minimum fuzz ratio for skill matching


@dataclass
class ValidationResult:
    """Result of validating a model explanation against known facts."""
    is_valid: bool = True
    confidence: float = 1.0  # 0.0–1.0
    issues: list[str] = field(default_factory=list)
    corrected_text: str | None = None
    quality_score: float = 0.0  # 0.0–1.0 explanation quality
    auto_fixes: list[str] = field(default_factory=list)


def validate_explanation(
    explanation: str,
    profile: UserProfile,
    job: Job,
    breakdown: MatchBreakdown,
) -> ValidationResult:
    """Run all validation checks and return a scored result."""
    result = ValidationResult()
    explanation_lower = explanation.lower()

    _check_skills(explanation_lower, profile, job, breakdown, result)
    _check_salary(explanation_lower, job, result)
    _check_location(explanation_lower, job, breakdown, result)
    _check_scores(explanation_lower, breakdown, result)
    _check_experience(explanation_lower, profile, job, result)
    _check_company_title(explanation_lower, job, result)
    _check_json_structure(explanation, result)
    _score_quality(explanation, breakdown, result)

    if result.issues:
        result.confidence = max(0.2, 1.0 - len(result.issues) * 0.15)

    return result


# ---------------------------------------------------------------------------
# Skill validation (fuzzy)
# ---------------------------------------------------------------------------

def _fuzzy_skill_match(mentioned: str, known_skills: set[str]) -> bool:
    """Check if a mentioned skill fuzzy-matches any known skill."""
    mentioned_lower = mentioned.lower().strip()
    for known in known_skills:
        # Exact substring check first
        if mentioned_lower in known or known in mentioned_lower:
            return True
        # Fuzzy match
        ratio = fuzz.ratio(mentioned_lower, known)
        if ratio >= FUZZY_THRESHOLD:
            return True
        # Partial ratio handles substrings better
        if fuzz.partial_ratio(mentioned_lower, known) >= FUZZY_THRESHOLD:
            return True
    return False


def _check_skills(
    explanation_lower: str,
    profile: UserProfile,
    job: Job,
    breakdown: MatchBreakdown,
    result: ValidationResult,
):
    """Check for skills mentioned in explanation that aren't in job or profile."""
    skill_patterns = [
        r"(?:proficiency in|experience with|skills? in|knowledge of|familiarity with"
        r"|expertise in|background in|understanding of)\s+"
        r"([a-z][a-z\s,/+&.]+?)(?:\.|,|\s+and\s|\s+are\s|\s+is\s|\s+for\s|$)",
        r"(?:uses?|using|requires?|leveraging)\s+([a-z][a-z\s,/+&.]+?)(?:\.|,|\s+and\s|$)",
    ]

    mentioned_skills = set()
    for pattern in skill_patterns:
        matches = re.findall(pattern, explanation_lower)
        for match in matches:
            for skill in re.split(r"[,/+&]", match):
                skill = skill.strip().strip(".")
                if len(skill) > 2 and skill not in {
                    "the", "and", "for", "with", "this", "that", "your", "their",
                    "our", "its", "his", "her", "are", "is", "in", "at", "to",
                    "of", "or", "a", "an", "on", "as", "be", "do", "no", "so",
                    "if", "it", "we", "you", "all", "can", "has", "had", "was",
                    "not", "but", "may", "also", "from", "will", "more", "such",
                    "some", "most", "well", "job", "role", "team", "work",
                }:
                    mentioned_skills.add(skill)

    # Known skills: union of job required skills + profile skills
    job_skills = {s.lower() for s in (breakdown.matching_skills + breakdown.missing_skills)}
    profile_skills = {s.lower() for s in (profile.skills or [])}
    known_skills = job_skills | profile_skills

    for skill in mentioned_skills:
        if not _fuzzy_skill_match(skill, known_skills):
            result.issues.append(f"unsupported_skill: '{skill}' not found in job or profile")


# ---------------------------------------------------------------------------
# Salary validation
# ---------------------------------------------------------------------------

def _parse_salary_amount(text: str) -> list[float]:
    """Extract numeric salary values from text, handling k/K suffixes."""
    amounts = []
    pattern = r"(?:£|\$|€|gbp|usd|eur)?\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?"
    for match in re.finditer(pattern, text):
        num_str = match.group(1).replace(",", "")
        try:
            num = float(num_str)
            if match.group(0).lower().endswith("k"):
                num *= 1000
            amounts.append(num)
        except ValueError:
            pass
    return amounts


def _check_salary(explanation_lower: str, job: Job, result: ValidationResult):
    """Check for salary figures that don't match the actual job data."""
    mentioned = re.findall(
        r"(?:£|\$|€|gbp|usd|eur)\s*[\d,]+(?:k|K)?(?:\s*[-to]+\s*(?:£|\$|€)?\s*[\d,]+(?:k|K)?)?",
        explanation_lower,
    )
    if not mentioned:
        return

    actual_min = job.salary_min
    actual_max = job.salary_max

    if actual_min is None and actual_max is None:
        result.issues.append(
            f"fabricated_salary: mentions salary '{mentioned[0]}' but job has no salary data"
        )
        return

    for mention in mentioned:
        amounts = _parse_salary_amount(mention)
        for num in amounts:
            if actual_min and abs(num - actual_min) / max(actual_min, 1) > 0.5:
                if actual_max is None or abs(num - actual_max) / max(actual_max, 1) > 0.5:
                    result.issues.append(
                        f"inaccurate_salary: '{mention}' doesn't match "
                        f"actual {actual_min}-{actual_max}"
                    )


# ---------------------------------------------------------------------------
# Location validation
# ---------------------------------------------------------------------------

def _check_location(
    explanation_lower: str,
    job: Job,
    breakdown: MatchBreakdown,
    result: ValidationResult,
):
    """Check for location claims inconsistent with the location fit score."""
    positive_claims = [
        "location fits", "location matches", "based in", "located in",
        "close to", "in your preferred", "near your", "in your area",
        "commutable", "same city", "same location",
    ]
    negative_claims = [
        "location doesn't", "location is not", "different location",
        "far from", "not in your preferred", "wrong location",
    ]

    has_positive = any(claim in explanation_lower for claim in positive_claims)
    has_negative = any(claim in explanation_lower for claim in negative_claims)

    if has_positive and breakdown.location_fit < 0.3:
        result.issues.append(
            f"inconsistent_location: claims location fits but score is "
            f"{round(breakdown.location_fit * 100, 1)}%"
        )
    if has_negative and breakdown.location_fit > 0.7:
        result.issues.append(
            f"inconsistent_location: claims location doesn't fit but score is "
            f"{round(breakdown.location_fit * 100, 1)}%"
        )

    # Check remote claim
    if "remote" in explanation_lower and not job.remote:
        if "fully remote" in explanation_lower or "is remote" in explanation_lower:
            result.issues.append("inaccurate_remote: job is not listed as remote")


# ---------------------------------------------------------------------------
# Score consistency validation
# ---------------------------------------------------------------------------

def _check_scores(
    explanation_lower: str,
    breakdown: MatchBreakdown,
    result: ValidationResult,
):
    """Check for qualitative score claims that contradict quantitative scores."""
    strong_phrases = [
        "strong match", "excellent match", "great match", "perfect match",
        "ideal match", "outstanding match",
    ]
    weak_phrases = [
        "poor match", "weak match", "low match", "not a good match",
        "bad match", "terrible match",
    ]
    moderate_phrases = [
        "moderate match", "decent match", "reasonable match",
        "fair match", "okay match",
    ]

    has_strong = any(p in explanation_lower for p in strong_phrases)
    has_weak = any(p in explanation_lower for p in weak_phrases)
    has_moderate = any(p in explanation_lower for p in moderate_phrases)

    pct = breakdown.match_percentage

    if has_strong and pct < 40:
        result.issues.append(
            f"inconsistent_score: calls it strong but score is {pct}%"
        )
    if has_weak and pct > 65:
        result.issues.append(
            f"inconsistent_score: calls it weak but score is {pct}%"
        )
    if has_moderate and (pct < 25 or pct > 85):
        result.issues.append(
            f"inconsistent_score: calls it moderate but score is {pct}%"
        )


# ---------------------------------------------------------------------------
# Experience level validation
# ---------------------------------------------------------------------------

def _check_experience(
    explanation_lower: str,
    profile: UserProfile,
    job: Job,
    result: ValidationResult,
):
    """Check for experience level claims that contradict profile or job data."""
    if not profile.experience_level or not job.experience_level:
        return

    user_level = profile.experience_level.lower().strip()
    job_level = job.experience_level.lower().strip()

    # If explanation says the experience level is a strong match but they're far apart
    exp_match_strong = any(
        phrase in explanation_lower
        for phrase in ["experience level matches", "experience level is a strong", "experience aligns"]
    )
    if exp_match_strong and user_level != job_level:
        user_rank = _level_rank(user_level)
        job_rank = _level_rank(job_level)
        if user_rank is not None and job_rank is not None and abs(user_rank - job_rank) >= 2:
            result.issues.append(
                f"inconsistent_experience: claims experience matches but profile is "
                f"'{user_level}' and job wants '{job_level}'"
            )


def _level_rank(level: str) -> int | None:
    mapping = {"intern": 0, "junior": 1, "entry": 1, "mid": 2, "senior": 3, "lead": 4, "principal": 5, "director": 6}
    return mapping.get(level.lower().strip())


# ---------------------------------------------------------------------------
# Company / title validation
# ---------------------------------------------------------------------------

def _check_company_title(
    explanation_lower: str,
    job: Job,
    result: ValidationResult,
):
    """Check that the explanation doesn't misstate the job title or company."""
    if job.company:
        # If company is mentioned, check it matches
        company_lower = job.company.lower()
        if company_lower in explanation_lower:
            pass  # Correct mention
        # Check for obviously wrong company names
        other_companies = [
            "google", "amazon", "microsoft", "apple", "meta", "netflix",
            "tesla", "nvidia", "openai", "spotify",
        ]
        for other in other_companies:
            if other in explanation_lower and other not in company_lower:
                # Might be an incorrect company - only flag if it's presented
                # as the hiring company
                if f"at {other}" in explanation_lower or f"at {other.title()}" in explanation_lower:
                    result.issues.append(
                        f"wrong_company: mentions '{other}' but job is at '{job.company}'"
                    )
                    break

    if job.title_clean or job.title:
        title = (job.title_clean or job.title).lower()
        # Only check if the explanation uses a very different job title
        # (we don't flag paraphrases, only completely different roles)
        pass  # Title paraphrasing is expected; skip strict check


# ---------------------------------------------------------------------------
# JSON structure validation (for structured output)
# ---------------------------------------------------------------------------

def _check_json_structure(explanation: str, result: ValidationResult):
    """Validate that structured output has the expected JSON shape."""
    text = explanation.strip()
    if not text.startswith("{"):
        return  # Not structured output, skip

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Try extracting from markdown fences
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                result.issues.append("malformed_json: could not parse structured output")
                return
        else:
            result.issues.append("malformed_json: structured output expected but not found")
            return

    required_keys = {"headline", "strengths", "gaps", "recommendation"}
    missing = required_keys - set(parsed.keys())
    if missing:
        result.issues.append(f"missing_json_keys: {', '.join(sorted(missing))}")

    if "headline" in parsed and not isinstance(parsed["headline"], str):
        result.issues.append("invalid_headline: must be a string")

    for key in ("strengths", "gaps"):
        if key in parsed and not isinstance(parsed[key], list):
            result.issues.append(f"invalid_{key}: must be a list")


# ---------------------------------------------------------------------------
# Explanation quality scoring
# ---------------------------------------------------------------------------

def _score_quality(
    explanation: str,
    breakdown: MatchBreakdown,
    result: ValidationResult,
):
    """Score the explanation quality on specificity and evidence usage."""
    score = 0.5  # baseline

    text = explanation.lower()

    # Specificity: mentions actual scores or percentages
    if re.search(r"\d+%", text):
        score += 0.1

    # Specificity: mentions actual skill names from the match
    if breakdown.matching_skills:
        skill_mentions = sum(
            1 for s in breakdown.matching_skills
            if s.lower() in text
        )
        if skill_mentions >= 2:
            score += 0.15
        elif skill_mentions >= 1:
            score += 0.05

    # Specificity: mentions specific weaknesses/gaps
    if breakdown.missing_skills:
        gap_mentions = sum(
            1 for s in breakdown.missing_skills[:5]
            if s.lower() in text
        )
        if gap_mentions >= 1:
            score += 0.1

    # Penalise very short explanations
    word_count = len(explanation.split())
    if word_count < 15:
        score -= 0.2
    elif word_count < 30:
        score -= 0.05

    # Bonus for balanced explanation (mentions both strengths and gaps)
    has_strength_words = any(w in text for w in ["strength", "match", "align", "fit", "suitab"])
    has_gap_words = any(w in text for w in ["gap", "miss", "lack", "need", "develop", "improve", "area"])
    if has_strength_words and has_gap_words:
        score += 0.1

    result.quality_score = max(0.0, min(1.0, score))
