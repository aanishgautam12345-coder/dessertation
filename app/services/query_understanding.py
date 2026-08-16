"""LLM-powered query understanding for job search.

Classifies search intent and expands queries with synonyms/related terms
before they hit the search pipeline. Uses Groq (LLaMA 3.3 70B) for fast
inference with MD5-based caching.

Falls back gracefully to the original query if the LLM is unavailable.
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
class QueryAnalysis:
    """Structured analysis of a search query."""
    intent: str = "hybrid"  # skill_search, title_search, company_search, location_search, hybrid
    expanded_terms: list[str] = field(default_factory=list)
    extracted_location: str | None = None
    extracted_experience: str | None = None
    extracted_salary_min: float | None = None
    confidence: float = 0.5
    raw_query: str = ""

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "expanded_terms": self.expanded_terms,
            "extracted_location": self.extracted_location,
            "extracted_experience": self.extracted_experience,
            "extracted_salary_min": self.extracted_salary_min,
            "confidence": self.confidence,
        }


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

_cache: dict[str, QueryAnalysis] = {}
MAX_CACHE_SIZE = 500


def _cache_key(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a search query analyst for a job matching platform.

Given a user's search query, produce a JSON object with:
- "intent": one of "skill_search", "title_search", "company_search", "location_search", "hybrid"
- "expanded_terms": list of 3-6 related terms/synonyms that should also be searched (e.g. "k8s" -> ["kubernetes", "helm", "container orchestration"])
- "extracted_location": city or country if mentioned, else null
- "extracted_experience": experience level if mentioned (junior/mid/senior/lead), else null
- "extracted_salary_min": minimum salary number if mentioned, else null
- "confidence": 0.0-1.0 how confident you are in the intent classification

Rules:
- "python" is a skill_search, not a title_search
- "react developer" is a skill_search (the skill is the key signal)
- "software engineer at Google" is a title_search with company_search
- "remote jobs in London" is a location_search
- "senior machine learning engineer" is a hybrid (title + skill)
- Keep expanded_terms relevant to JOB SEARCH specifically
- Only include terms you are confident are related

Respond with ONLY the JSON object, no explanation."""

_USER_PROMPT = f'Analyze this job search query: "{{query}}"'


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def analyse_query(query: str, use_cache: bool = True) -> QueryAnalysis:
    """Classify intent and expand a search query using LLM.

    Returns QueryAnalysis with intent, expanded terms, and extracted filters.
    Falls back to a basic QueryAnalysis on any error.
    """
    query = query.strip()
    if not query:
        return QueryAnalysis(raw_query=query)

    # Cache lookup
    if use_cache:
        key = _cache_key(query)
        if key in _cache:
            return _cache[key]

    # Fast path: very short queries with known patterns
    basic = _basic_analysis(query)
    if basic and basic.confidence >= 0.8:
        if use_cache:
            _cache[_cache_key(query)] = basic
        return basic

    # LLM path
    try:
        result = _llm_analyse(query)
        if use_cache and len(_cache) < MAX_CACHE_SIZE:
            _cache[_cache_key(query)] = result
        return result
    except Exception as e:
        logger.warning(f"Query understanding failed, using fallback: {e}")
        fallback = basic or QueryAnalysis(raw_query=query, expanded_terms=[query.lower()])
        return fallback


def _basic_analysis(query: str) -> QueryAnalysis | None:
    """Fast regex-based analysis for obvious queries, avoiding LLM call."""
    q = query.lower().strip()
    tokens = q.split()

    # Single known skill -> skill_search
    from app.processing.skills import ALL_SKILLS
    if q in ALL_SKILLS:
        return QueryAnalysis(
            intent="skill_search",
            expanded_terms=[q],
            confidence=0.85,
            raw_query=query,
        )

    # "X developer/engineer/architect" pattern -> skill_search
    dev_pattern = re.match(r"^(.+?)\s+(developer|engineer|architect|programmer|specialist)$", q)
    if dev_pattern:
        skill = dev_pattern.group(1).strip()
        return QueryAnalysis(
            intent="skill_search",
            expanded_terms=[skill, q],
            confidence=0.8,
            raw_query=query,
        )

    # Location patterns
    loc_pattern = re.match(r"^(?:remote|hybrid|onsite)\s+(?:jobs?\s+(?:in|near)\s+)?(.+)$", q)
    if loc_pattern:
        return QueryAnalysis(
            intent="location_search",
            extracted_location=loc_pattern.group(1).strip(),
            confidence=0.8,
            raw_query=query,
        )

    return None


def _llm_analyse(query: str) -> QueryAnalysis:
    """Call Groq LLM for query analysis."""
    client = _get_client()
    settings = get_settings()

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f'Analyze this job search query: "{query}"'},
        ],
        temperature=0.1,
        max_tokens=300,
    )

    raw = response.choices[0].message.content or "{}"
    data = _parse_response(raw)

    return QueryAnalysis(
        intent=data.get("intent", "hybrid"),
        expanded_terms=data.get("expanded_terms", []),
        extracted_location=data.get("extracted_location"),
        extracted_experience=data.get("extracted_experience"),
        extracted_salary_min=data.get("extracted_salary_min"),
        confidence=float(data.get("confidence", 0.5)),
        raw_query=query,
    )


def _parse_response(raw: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning(f"Failed to parse LLM response: {raw[:200]}")
        return {}


# ---------------------------------------------------------------------------
# Query expansion helper
# ---------------------------------------------------------------------------

def get_expanded_aliases(query: str) -> list[str]:
    """Get expanded search terms for a query.

    Returns a list of terms to search for, combining the original query
    with LLM-expanded terms. Deduplicates and preserves order.
    """
    analysis = analyse_query(query)
    terms = [query.lower().strip()]
    for t in analysis.expanded_terms:
        t = t.lower().strip()
        if t and t not in terms:
            terms.append(t)
    return terms
