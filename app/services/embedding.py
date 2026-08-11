"""Generates embeddings for jobs, profiles and search queries via sentence-transformers
(BAAI/bge-base-en-v1.5, 768 dims). Switched from all-MiniLM-L6-v2 - retrieval was noticeably
better on job matching."""

import re
import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the model once and cache it in memory."""
    settings = get_settings()
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    model = SentenceTransformer(settings.embedding_model)
    logger.info("Embedding model loaded")
    return model


# ── Boilerplate patterns to strip from job descriptions ──
BOILERPLATE_PATTERNS = [
    # Equal opportunity / diversity statements
    r"(?i)equal\s+opportunity\s+employer.*",
    r"(?i)we\s+are\s+(an?\s+)?equal\s+opportunity.*",
    r"(?i)(?:we|the company)\s+(?:is|are)\s+committed\s+to\s+(?:diversity|equal).*",
    r"(?i)without\s+regard\s+to\s+race,?\s+color.*",
    r"(?i)all\s+qualified\s+applicants?\s+will\s+receive\s+consideration.*",
    # Benefits boilerplate
    r"(?i)(?:we|our company)\s+offer(?:s)?\s+(?:a\s+)?competitive\s+(?:salary|benefits|compensation).*",
    r"(?i)benefits?\s+(?:include|package).*?(?:dental|vision|401k|retirement|insurance).*",
    # Application instructions
    r"(?i)(?:how\s+to\s+)?apply\s+(?:now|today|here).*",
    r"(?i)please\s+(?:send|submit|forward)\s+your\s+(?:resume|cv).*",
    r"(?i)click\s+(?:here|apply)\s+to.*",
    # Legal / disclaimer
    r"(?i)this\s+(?:job|position)\s+(?:description|posting)\s+(?:is\s+not|does\s+not).*",
    r"(?i)disclaimer.*",
]

COMPILED_BOILERPLATE = [re.compile(p, re.MULTILINE | re.DOTALL) for p in BOILERPLATE_PATTERNS]


def _strip_boilerplate(text: str) -> str:
    """Strip the legal/benefits/apply-now noise that dilutes the embedding signal."""
    for pattern in COMPILED_BOILERPLATE:
        text = pattern.sub("", text)

    # Also strip the last 25% of very long descriptions - usually
    # benefits, disclaimers, and application instructions live at the end
    lines = text.strip().split("\n")
    if len(lines) > 20:
        cutoff = int(len(lines) * 0.75)
        text = "\n".join(lines[:cutoff])

    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def generate_embedding(text: str, is_query: bool = False) -> list[float]:
    """Embed a piece of text. Pass is_query=True for search queries/profiles (BGE wants a
    prefix on those), leave False for job descriptions - they're the "documents" being searched."""
    if not text or not text.strip():
        return [0.0] * get_settings().embedding_dim

    if is_query:
        text = "Represent this sentence: " + text

    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(
    texts: list[str],
    batch_size: int = 32,
    is_query: bool = False,
) -> list[list[float]]:
    """Same as generate_embedding but batched for speed."""
    model = _get_model()

    clean_texts = []
    for t in texts:
        if not t or not t.strip():
            t = "empty"
        if is_query:
            t = "Represent this sentence: " + t
        clean_texts.append(t)

    embeddings = model.encode(
        clean_texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return embeddings.tolist()


def build_job_text(title: str, description: str, skills: list[str] | None = None,
                   location_city: str | None = None, location_country: str | None = None,
                   remote: bool = False) -> str:
    """Combine job fields into one string for embedding."""
    parts = []

    # title twice so it dominates the embedding signal
    clean_title = title.strip() if title else ""
    if clean_title:
        parts.append(clean_title)
        parts.append(clean_title)

    # Include location for geographic relevance in vector search
    location_parts = []
    if location_city:
        location_parts.append(location_city)
    if location_country:
        location_parts.append(location_country)
    if location_parts:
        parts.append("Location: " + ", ".join(location_parts))
    if remote:
        parts.append("Remote available")

    if skills:
        parts.append("Required skills: " + ", ".join(skills))

    if description:
        cleaned = _strip_boilerplate(description)
        # first 1500 chars only - the important stuff is usually at the top,
        # and long text just dilutes the embedding
        parts.append(cleaned[:1500])

    return " | ".join(parts)


def build_profile_text(
    headline: str | None,
    skills: list[str] | None,
    career_interests: str | None,
    experience_level: str | None,
) -> str:
    """Combine profile fields into one string, embedded with is_query=True since the
    profile is effectively the search query looking for matching jobs."""
    parts = []

    if headline:
        parts.append(headline)
        parts.append(headline)

    if experience_level:
        parts.append(f"Experience level: {experience_level}")

    if skills:
        parts.append("Skills: " + ", ".join(skills))

    if career_interests:
        parts.append(career_interests)

    return " | ".join(parts) if parts else "general job seeker"
