"""LLM-based result re-scoring using Groq.

Takes top results from any search pipeline and re-scores them using the full
profile+job context. Catches nuances that rule-based scoring misses (e.g. a
"machine learning engineer" profile matching a "data scientist" job posting).

Uses batch prompting (all candidates in one LLM call) for efficiency.
Falls back to original scores if LLM is unavailable.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field

from openai import OpenAI, BadRequestError

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------

@dataclass
class LLMRerankResult:
    """Re-scored result for a single job."""
    job_id: str
    llm_score: float  # 0.0 - 1.0
    reason: str = ""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set")
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_api_base,
        )
    return _client


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_cache: dict[str, list[LLMRerankResult]] = {}
MAX_CACHE_SIZE = 200


def _cache_key(profile_text: str, job_ids: list[str]) -> str:
    combined = profile_text + "|".join(sorted(job_ids))
    return hashlib.md5(combined.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a job matching expert. Given a user profile and a list of candidate jobs,
re-score each job's relevance to this user on a scale of 0.0 to 1.0.

Consider:
- Skill match (does the user have the required skills?)
- Experience level alignment (junior user vs senior role = low score)
- Career interest alignment (does this match their stated goals?)
- Location/remote fit
- Salary alignment if available

User Profile:
{profile}

For each job, return a JSON array of objects with:
- "job_id": the job ID
- "score": 0.0-1.0 relevance score
- "reason": one sentence explaining the score

Respond with ONLY the JSON array, no explanation."""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def llm_rerank(
    profile_text: str,
    candidates: list[dict],
    top_n: int | None = None,
    blend_weight: float = 0.4,
    use_cache: bool = True,
) -> list[dict]:
    """Re-score candidates using LLM with full profile context.

    Args:
        profile_text: Summary of user profile for context
        candidates: List of job dicts with at least 'id', 'title', 'company'
        top_n: Limit output to top N results
        blend_weight: Weight for LLM score in final blend (0.0-1.0)
        use_cache: Whether to use MD5 cache

    Returns:
        Candidates with 'llm_score' and 'blended_score' fields added.
        Sorted by blended_score descending.
    """
    if not candidates:
        return candidates

    # Check cache
    job_ids = [c.get("id", "") for c in candidates]
    if use_cache:
        key = _cache_key(profile_text, job_ids)
        cached = _cache.get(key)
        if cached is not None:
            return _apply_scores(candidates, cached, blend_weight, top_n)

    # Call LLM
    try:
        results = _llm_rerank(profile_text, candidates)
        if use_cache and len(_cache) < MAX_CACHE_SIZE:
            _cache[_cache_key(profile_text, job_ids)] = results
        return _apply_scores(candidates, results, blend_weight, top_n)
    except Exception as e:
        logger.warning(f"LLM reranking failed, using original scores: {e}")
        # Mark as no LLM score
        for c in candidates:
            c["llm_score"] = None
            c["blended_score"] = c.get("ranking_score", c.get("search_relevance_score", 0))
        if top_n:
            return candidates[:top_n]
        return candidates


def _apply_scores(
    candidates: list[dict],
    llm_results: list[LLMRerankResult],
    blend_weight: float,
    top_n: int | None,
) -> list[dict]:
    """Apply LLM scores to candidates and compute blended scores."""
    llm_map = {r.job_id: r for r in llm_results}

    for c in candidates:
        jid = c.get("id", "")
        llm_r = llm_map.get(jid)
        if llm_r:
            c["llm_score"] = llm_r.llm_score
            c["llm_reason"] = llm_r.reason
            original = c.get("ranking_score", c.get("search_relevance_score", 0)) / 100.0
            blended = (1.0 - blend_weight) * original + blend_weight * llm_r.llm_score
            c["blended_score"] = round(blended * 100, 1)
        else:
            c["llm_score"] = None
            c["blended_score"] = c.get("ranking_score", c.get("search_relevance_score", 0))

    # Sort by blended score
    candidates.sort(key=lambda x: x.get("blended_score", 0), reverse=True)

    if top_n:
        return candidates[:top_n]
    return candidates


def _llm_rerank(profile_text: str, candidates: list[dict]) -> list[LLMRerankResult]:
    """Call Groq LLM for batch re-scoring."""
    client = _get_client()
    settings = get_settings()

    # Build candidate descriptions
    job_descriptions = []
    for c in candidates:
        parts = [
            f"ID: {c.get('id', 'unknown')}",
            f"Title: {c.get('title', 'Unknown')}",
            f"Company: {c.get('company', 'Unknown')}",
        ]
        if c.get("location_city") or c.get("location_country"):
            loc = ", ".join(filter(None, [c.get("location_city"), c.get("location_country")]))
            parts.append(f"Location: {loc}")
        if c.get("remote"):
            parts.append("Remote: yes")
        skills = c.get("skills")
        if skills:
            if isinstance(skills, list):
                skills = ", ".join(skills[:10])
            parts.append(f"Skills: {skills}")
        desc = c.get("description", "")
        if desc:
            parts.append(f"Description: {desc[:300]}")
        job_descriptions.append(" | ".join(parts))

    jobs_text = "\n".join(f"{i+1}. {desc}" for i, desc in enumerate(job_descriptions))

    system_prompt = _SYSTEM_PROMPT.format(profile=profile_text)

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Re-score these {len(candidates)} candidate jobs:\n\n{jobs_text}"},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content or "[]"
    return _parse_response(raw, candidates)


def _parse_response(raw: str, candidates: list[dict]) -> list[LLMRerankResult]:
    """Parse LLM JSON response into LLMRerankResult list."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM rerank response: {raw[:200]}")
                return []
        else:
            logger.warning(f"Failed to parse LLM rerank response: {raw[:200]}")
            return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        jid = str(item.get("job_id", ""))
        score = float(item.get("score", 0.5))
        reason = str(item.get("reason", ""))
        results.append(LLMRerankResult(
            job_id=jid,
            llm_score=max(0.0, min(1.0, score)),
            reason=reason,
        ))

    return results
