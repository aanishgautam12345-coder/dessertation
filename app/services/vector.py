"""Vector similarity helpers - pgvector's <=> operator, with a numpy fallback for
when it's not available (e.g. SQLite in tests)."""

import json
import logging
import numpy as np
from sqlalchemy import Float, select, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors using numpy."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def embedding_to_jsonb(embedding: list[float]) -> list[float]:
    """Convert embedding list to JSONB-compatible format (just a list)."""
    return embedding


def jsonb_to_embedding(data) -> list[float] | None:
    """Convert JSONB data back to embedding list."""
    if data is None:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def find_similar_by_embedding(
    db: Session,
    model_class,
    query_embedding: list[float],
    embedding_column,
    limit: int = 10,
    exclude_id=None,
) -> list:
    """Find the most similar records to query_embedding. Returns (record, similarity)
    tuples, most similar first."""
    try:
        return _pgvector_search(
            db, model_class, query_embedding, embedding_column, limit, exclude_id
        )
    except Exception as e:
        logger.debug(f"pgvector operator not available, falling back to Python: {e}")
        return _python_search(
            db, model_class, query_embedding, embedding_column, limit, exclude_id
        )


def _pgvector_search(
    db: Session,
    model_class,
    query_embedding: list[float],
    embedding_column,
    limit: int = 10,
    exclude_id=None,
) -> list:
    """Use pgvector's <=> cosine distance operator for similarity search."""
    # pgvector cosine distance: a <=> b = 1 - cosine_similarity(a, b)
    # So smaller distance = more similar
    distance_expr = embedding_column.op("<=>", return_type=Float)(query_embedding)

    stmt = (
        select(model_class, distance_expr.label("distance"))
        .where(embedding_column.isnot(None))
    )

    if exclude_id is not None:
        stmt = stmt.where(model_class.id != exclude_id)

    stmt = stmt.order_by(distance_expr.asc()).limit(limit)

    results = db.execute(stmt).all()

    return [(row[0], 1.0 - row.distance) for row in results]


def _python_search(
    db: Session,
    model_class,
    query_embedding: list[float],
    embedding_column,
    limit: int = 10,
    exclude_id=None,
) -> list:
    """Fallback: compute cosine similarity in Python using numpy."""
    q = select(model_class).where(embedding_column.isnot(None))
    if exclude_id is not None:
        q = q.where(model_class.id != exclude_id)

    results = db.execute(q).scalars().all()

    scored = []
    query_vec = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []

    for record in results:
        emb = getattr(record, embedding_column.key)
        if emb is None:
            continue
        emb_vec = np.array(emb, dtype=np.float32)
        emb_norm = np.linalg.norm(emb_vec)
        if emb_norm == 0:
            continue
        sim = float(np.dot(query_vec, emb_vec) / (query_norm * emb_norm))
        scored.append((record, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
