"""Re-ranks candidates with a cross-encoder (query+document pairs scored together,
more accurate than plain cosine similarity). Lightweight model, runs fine on CPU;
just returns the original order if it's not available."""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Model config - kept lightweight for CPU inference
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MAX_SEQUENCE_LENGTH = 512


@dataclass
class RerankResult:
    """A single reranked result."""
    index: int        # Original position in the candidate list
    score: float      # Cross-encoder relevance score
    original_score: float  # Pre-reranking score for comparison


@lru_cache(maxsize=1)
def _get_reranker():
    """Load the cross-encoder model once and cache it."""
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        model = CrossEncoder(RERANKER_MODEL, max_length=MAX_SEQUENCE_LENGTH)
        logger.info("Reranker model loaded.")
        return model
    except Exception as e:
        logger.warning(f"Failed to load reranker model: {e}. Reranking disabled.")
        return None


def rerank_candidates(
    query: str,
    candidates: list[dict],
    top_n: int | None = None,
    score_field: str = "title",
) -> list[dict]:
    """Re-rank candidates by cross-encoder relevance to query. Adds a "rerank_score"
    field to each dict; score_field picks which key to use as the document text."""
    model = _get_reranker()

    if model is None or not candidates:
        return candidates

    pairs = []
    for c in candidates:
        doc_text = c.get(score_field) or c.get("title") or ""
        company = c.get("company", "")
        location = c.get("location_city") or c.get("location_country") or ""
        parts = [doc_text, company, location]
        skills = c.get("skills")
        if skills:
            if isinstance(skills, list):
                skills = ", ".join(skills)
            parts.append(f"Skills: {skills}")
        description = c.get("description")
        if description:
            parts.append(description[:300])
        doc_text = " | ".join(p for p in parts if p).strip()
        pairs.append((query, doc_text[:MAX_SEQUENCE_LENGTH]))

    try:
        scores = model.predict(pairs, show_progress_bar=False)
    except Exception as e:
        logger.warning(f"Reranking failed: {e}. Returning original order.")
        return candidates

    for i, (candidate, score) in enumerate(zip(candidates, scores)):
        candidate["rerank_score"] = float(score)
        candidate["rerank_original_index"] = i

    reranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)

    if top_n is not None:
        reranked = reranked[:top_n]

    return reranked


def is_reranker_available() -> bool:
    """Check if the reranker model is loaded and available."""
    return _get_reranker() is not None
