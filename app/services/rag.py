"""Explanation engine.

Turns a match-score breakdown into a structured, factually-grounded explanation.
The model receives ONLY pre-computed evidence (profile + job + breakdown) and is
prompted to reason step-by-step before producing the final output.

Key improvements over the basic version:
  1. Chain-of-thought reasoning before generating the explanation
  2. Adaptive prompt selection based on match quality tier
  3. Structured output with headline, strengths, gaps, and recommendation
  4. Retry with self-correction when validation fails
  5. Fuzzy-validated skill claims via the enhanced validator
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field

from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    PermissionDeniedError,
    BadRequestError,
)

from app.config import get_settings
from app.models.job import Job
from app.models.user import UserProfile
from app.services.recommendation import MatchBreakdown
from app.services.explanation_validator import validate_explanation, ValidationResult

logger = logging.getLogger(__name__)

_client: OpenAI | None = None
MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------

@dataclass
class ExplanationResult:
    """Structured explanation returned by the explanation engine."""
    headline: str = ""
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendation: str = ""
    raw_text: str = ""  # Full plain-text explanation (backward compat)
    confidence: float = 0.0
    validation_issues: list[str] = field(default_factory=list)
    match_tier: str = "medium"  # high / medium / low
    error: str | None = None  # Set when fallback was due to an error

    def to_text(self) -> str:
        """Flatten to a single plain-English string (backward compatible)."""
        parts = [self.headline] if self.headline else []
        if self.strengths:
            parts.append("Strengths: " + "; ".join(self.strengths) + ".")
        if self.gaps:
            parts.append("Gaps: " + "; ".join(self.gaps) + ".")
        if self.recommendation:
            parts.append(self.recommendation)
        return " ".join(parts) if parts else self.raw_text


# ---------------------------------------------------------------------------
# Client management
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY not set in .env. "
                "Get a key at https://console.groq.com/keys"
            )
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_api_base,
        )
    return _client


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_explanation_cache: dict[str, ExplanationResult] = {}


def _cache_key(profile: UserProfile, job: Job, breakdown: MatchBreakdown) -> str:
    key_parts = [
        str(profile.user_id),
        str(job.id),
        str(breakdown.match_percentage),
        str(breakdown.semantic_similarity),
        str(breakdown.skill_overlap),
    ]
    return hashlib.md5("|".join(key_parts).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Match tier classification
# ---------------------------------------------------------------------------

def _classify_tier(breakdown: MatchBreakdown) -> str:
    if breakdown.match_percentage >= 75:
        return "high"
    if breakdown.match_percentage >= 45:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Evidence assembly
# ---------------------------------------------------------------------------

def _build_evidence_block(
    profile: UserProfile,
    job: Job,
    breakdown: MatchBreakdown,
) -> str:
    """Assemble the factual evidence block shared across all prompts."""
    matching_skills = ", ".join(breakdown.matching_skills) if breakdown.matching_skills else "none identified"
    missing_skills = ", ".join(breakdown.missing_skills[:8]) if breakdown.missing_skills else "none"

    location_desc = "remote" if job.remote else (
        job.location_city or job.location_country or "unspecified location"
    )
    salary_desc = (
        f"{job.salary_min or '?'}-{job.salary_max or '?'} {job.salary_currency or ''}"
        if (job.salary_min or job.salary_max) else "not disclosed"
    )
    user_min_salary = (
        f"{profile.min_salary} {profile.salary_currency}"
        if profile.min_salary else "not specified"
    )

    # Truncated job description for context (first 600 chars)
    job_desc_snippet = ""
    if job.description_clean:
        job_desc_snippet = job.description_clean[:600]
    elif job.description:
        job_desc_snippet = job.description[:600]

    return f"""CANDIDATE PROFILE:
- Headline: {profile.headline or 'not specified'}
- Skills: {', '.join(profile.skills) if profile.skills else 'not specified'}
- Experience level: {profile.experience_level or 'not specified'} ({profile.experience_years or '?'} years)
- Preferred locations: {', '.join(profile.preferred_locations) if profile.preferred_locations else 'not specified'}
- Minimum salary expectation: {user_min_salary}
- Career interests: {profile.career_interests or 'not specified'}

JOB:
- Title: {job.title_clean or job.title}
- Company: {job.company or 'not specified'}
- Location: {location_desc}
- Salary: {salary_desc}
- Category: {job.category or 'not specified'}
- Job type: {job.job_type or 'not specified'}
- Experience level: {job.experience_level or 'not specified'}

JOB DESCRIPTION SNIPPET:
{job_desc_snippet if job_desc_snippet else 'not available'}

COMPUTED MATCH EVIDENCE (pre-scored - explain, do not re-judge):
- Overall match: {breakdown.match_percentage}%
- Semantic relevance: {round(breakdown.semantic_similarity * 100, 1)}%
- Matching skills: {matching_skills}
- Missing skills the job wants: {missing_skills}
- Location fit: {round(breakdown.location_fit * 100, 1)}%
- Salary fit: {round(breakdown.salary_fit * 100, 1)}%
- Experience level fit: {round(breakdown.experience_fit * 100, 1)}%
- Job type fit: {round(breakdown.job_type_fit * 100, 1)}%"""


# ---------------------------------------------------------------------------
# Prompt templates (adaptive per tier)
# ---------------------------------------------------------------------------

_SYSTEM_BASE = (
    "You are an expert job-match analyst. You explain WHY a job was recommended "
    "to a candidate using ONLY the facts provided. Never invent information. "
    "Be specific: reference actual skills, scores, and job details."
)

_COT_SUFFIX = """

STEP-BY-STEP (internal reasoning, do not output this):
1. Identify the top 2-3 strengths of this match.
2. Identify the top 1-2 gaps or concerns.
3. Decide the overall recommendation tone.

OUTPUT (valid JSON only):
{
  "headline": "<one sentence summarising the match>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "gaps": ["<gap 1>", ...],
  "recommendation": "<1-2 sentence actionable recommendation>"
}"""


def _prompt_high_match(evidence: str) -> str:
    return f"""You are explaining why a job is a STRONG match for a candidate.

{evidence}

Write a compelling explanation that:
- Leads with the strongest alignment signals (semantic match, shared skills)
- Notes any minor gaps but frames them as growth opportunities
- Ends with a clear recommendation to apply

{_COT_SUFFIX}"""


def _prompt_medium_match(evidence: str) -> str:
    return f"""You are explaining why a job is a MODERATE match for a candidate.

{evidence}

Write a balanced explanation that:
- Highlights genuine strengths (matched skills, relevant experience)
- Honestly notes gaps (missing skills, location/salary mismatches)
- Suggests whether applying is worthwhile and what to watch for

{_COT_SUFFIX}"""


def _prompt_low_match(evidence: str) -> str:
    return f"""You are explaining why a job is a WEAK match for a candidate.

{evidence}

Write an honest, constructive explanation that:
- Acknowledges the low match score upfront
- Points out whatever genuine alignment exists (if any)
- Clearly explains the main mismatches
- Suggests whether applying is still worth it or not

{_COT_SUFFIX}"""


def _select_prompt(tier: str, evidence: str, breakdown: MatchBreakdown) -> tuple[str, str]:
    """Return (system_msg, user_prompt) for the given tier."""
    if tier == "high":
        return _SYSTEM_BASE, _prompt_high_match(evidence)
    if tier == "low":
        return _SYSTEM_BASE, _prompt_low_match(evidence)
    # medium is default
    return _SYSTEM_BASE, _prompt_medium_match(evidence)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_structured_response(raw: str) -> dict:
    """Best-effort parse of the model JSON response. Falls back gracefully."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from surrounding text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}


def _to_explanation_result(
    parsed: dict,
    raw: str,
    tier: str,
    validation: ValidationResult,
) -> ExplanationResult:
    return ExplanationResult(
        headline=parsed.get("headline", ""),
        strengths=parsed.get("strengths", []),
        gaps=parsed.get("gaps", []),
        recommendation=parsed.get("recommendation", ""),
        raw_text=raw.strip(),
        confidence=validation.confidence,
        validation_issues=validation.issues,
        match_tier=tier,
    )


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def generate_explanation(
    profile: UserProfile,
    job: Job,
    breakdown: MatchBreakdown,
    model: str = "",
    validate: bool = True,
) -> ExplanationResult:
    """Generate a structured, validated explanation for a job match.

    Returns an ExplanationResult with structured fields and a plain-text
    fallback. Uses adaptive prompting, chain-of-thought, retry with
    self-correction, and validation against ground truth.
    """
    cache_key = _cache_key(profile, job, breakdown)
    if cache_key in _explanation_cache:
        return _explanation_cache[cache_key]

    tier = _classify_tier(breakdown)
    evidence = _build_evidence_block(profile, job, breakdown)
    settings = get_settings()
    model_name = model or settings.groq_model

    result = _generate_with_retry(
        evidence, tier, breakdown, model_name, profile, job, validate
    )

    if result.raw_text and len(_explanation_cache) < 256:
        _explanation_cache[cache_key] = result

    return result


def _is_retryable_error(exc: Exception) -> bool:
    """Return True if the provider error is transient and worth retrying."""
    # Auth / permission / bad-request are permanent - retrying won't help
    if isinstance(exc, (AuthenticationError, PermissionDeniedError, BadRequestError)):
        return False
    # Rate limits are transient - brief backoff may help
    if isinstance(exc, RateLimitError):
        return True
    # Everything else (network, timeout, server) is worth retrying
    return True


def _error_to_message(exc: Exception) -> str:
    """Human-readable short description of a provider error."""
    if isinstance(exc, AuthenticationError):
        return "invalid API key - check GROQ_API_KEY in .env"
    if isinstance(exc, RateLimitError):
        return "rate limited - try again shortly"
    if isinstance(exc, PermissionDeniedError):
        return "API key lacks required permissions"
    if isinstance(exc, BadRequestError):
        return f"bad request: {exc}"
    return f"{type(exc).__name__}: {exc}"


def _generate_with_retry(
    evidence: str,
    tier: str,
    breakdown: MatchBreakdown,
    model_name: str,
    profile: UserProfile,
    job: Job,
    validate: bool,
) -> ExplanationResult:
    """Generate with up to MAX_RETRIES attempts, using validation feedback to self-correct."""
    last_result = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            system_msg, user_prompt = _select_prompt(tier, evidence, breakdown)

            # On retry, append validation feedback to the prompt
            if attempt > 0 and last_result and last_result.validation_issues:
                feedback = "; ".join(last_result.validation_issues)
                user_prompt += (
                    f"\n\nPREVIOUS ATTEMPT had these issues: {feedback}. "
                    "Fix them and regenerate the JSON output."
                )

            client = _get_client()
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=400,
                temperature=0.3 if attempt == 0 else 0.1,
            )
            raw = response.choices[0].message.content if response.choices else None

            if not isinstance(raw, str) or not raw.strip():
                logger.warning("Model returned empty output (attempt %d)", attempt + 1)
                last_result = ExplanationResult(
                    raw_text=_fallback_explanation(breakdown),
                    match_tier=tier,
                )
                continue

            parsed = _parse_structured_response(raw)

            if validate:
                # Validate the raw text portion
                validation = validate_explanation(raw, profile, job, breakdown)
                result = _to_explanation_result(parsed, raw, tier, validation)

                if validation.is_valid:
                    return result

                logger.warning(
                    "Validation failed (attempt %d, confidence=%.2f): %s",
                    attempt + 1,
                    validation.confidence,
                    validation.issues,
                )
                last_result = result
            else:
                return _to_explanation_result(parsed, raw, tier, ValidationResult())

        except Exception as e:
            logger.warning(
                "Model call failed (attempt %d, %s): %s",
                attempt + 1,
                type(e).__name__,
                e,
            )
            # Non-retryable errors: fail immediately
            if not _is_retryable_error(e):
                return ExplanationResult(
                    raw_text=_fallback_explanation(breakdown),
                    match_tier=tier,
                    error=_error_to_message(e),
                )
            last_result = ExplanationResult(
                raw_text=_fallback_explanation(breakdown),
                match_tier=tier,
                error=_error_to_message(e),
            )

    # All retries exhausted - if validation kept failing, use fallback template
    if last_result and not last_result.validation_issues:
        return last_result
    return ExplanationResult(
        raw_text=_fallback_explanation(breakdown),
        match_tier=tier,
        confidence=last_result.confidence if last_result else 0.0,
        validation_issues=last_result.validation_issues if last_result else [],
    )


def _fallback_explanation(breakdown: MatchBreakdown) -> str:
    """Template-based fallback when the model is unavailable."""
    parts = [f"This job scored {breakdown.match_percentage}% overall."]

    if breakdown.matching_skills:
        parts.append(f"It matches your skills in {', '.join(breakdown.matching_skills[:3])}.")

    if breakdown.missing_skills:
        parts.append(f"You may need to develop: {', '.join(breakdown.missing_skills[:3])}.")

    if breakdown.location_fit >= 0.9:
        parts.append("The location fits your preferences well.")
    elif breakdown.location_fit <= 0.1:
        parts.append("The location does not match your preferences.")

    if breakdown.salary_fit >= 0.9:
        parts.append("The salary meets your expectations.")
    elif breakdown.salary_fit <= 0.3:
        parts.append("The salary may not meet your expectations.")

    if breakdown.experience_fit >= 0.9:
        parts.append("Your experience level is a strong fit.")
    elif breakdown.experience_fit <= 0.3:
        parts.append("The experience level may not align well.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Backward-compatible helper
# ---------------------------------------------------------------------------

def generate_explanation_text(
    profile: UserProfile,
    job: Job,
    breakdown: MatchBreakdown,
    model: str = "",
    validate: bool = True,
) -> str:
    """Convenience wrapper that returns a plain string (backward compatible)."""
    result = generate_explanation(profile, job, breakdown, model, validate)
    return result.to_text()
