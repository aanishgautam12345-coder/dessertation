# JOBMATCH — COMPLETE DIAGRAM SPECIFICATION
## Extracted from Actual Implementation Evidence

---

# 1. PROJECT IDENTITY

| Item | Extracted Information | Evidence | Confidence |
|------|----------------------|----------|------------|
| System Name | JobMatch | `app/main.py` FastAPI title: "JobMatch" | CONFIRMED |
| Full Name | Job Vacancy Aggregator and Personalised Recommendation System | `app/main.py` FastAPI description | CONFIRMED |
| Purpose | Aggregate job vacancies from multiple sources, normalise data, generate personalised recommendations using AI/ML, and deliver notifications | All source files | CONFIRMED |
| Target Users | Job seekers (registered users), Administrators | Auth system, admin routes | CONFIRMED |
| Problem Solved | Manual job searching is inefficient; users need personalised matching across multiple job boards | Architecture evidence | STRONGLY INFERRED |
| Language | Python 3.11+ | `requirements.txt`, type hints (`str | None`) | CONFIRMED |
| Dual Frontend | FastAPI (REST API on port 8000) + Flask (Web UI on port 5000) | `app/main.py`, `run.py` | CONFIRMED |
| Database | PostgreSQL 16 + pgvector extension | `docker-compose.yml`, `app/database.py` | CONFIRMED |
| AI/ML Models | BAAI/bge-base-en-v1.5 (embeddings), llama-3.3-70b-versatile via Groq (LLM), cross-encoder/ms-marco-MiniLM-L-6-v2 (reranker) | `app/config.py`, `app/services/embedding.py`, `app/services/reranker.py`, `app/services/rag.py` | CONFIRMED |

---

# 2. COMPLETE TECHNOLOGY INVENTORY

| Technology | Category | Actual Role | Component | Evidence | Confidence |
|------------|----------|-------------|-----------|----------|------------|
| Python 3.11+ | Language | Primary programming language | All | Type hints, f-strings, `str \| None` union syntax | CONFIRMED |
| FastAPI 0.115.6 | Backend Framework | REST API server (port 8000) | `app/main.py` | Import, app instantiation | CONFIRMED |
| Flask 3.1.0 | Frontend Framework | Web UI server (port 5000) | `webapp/app.py`, `run.py` | Import, app factory | CONFIRMED |
| SQLAlchemy 2.0.36 | ORM | Database access layer | `app/database.py`, all models | DeclarativeBase, mapped_column | CONFIRMED |
| PostgreSQL 16 | Database | Primary persistent storage | `docker-compose.yml` | pgvector/pgvector:pg16 image | CONFIRMED |
| pgvector 0.3.6 | Vector Extension | Vector similarity search in PostgreSQL | `app/database.py` (`CREATE EXTENSION vector`), `app/services/vector.py` | `<=>` operator usage | CONFIRMED |
| Alembic 1.14.1 | Migration Tool | Database schema migrations | `alembic/` directory, 7 migration files | CONFIRMED |
| BAAI/bge-base-en-v1.5 | Embedding Model | 768-dim text embeddings | `app/services/embedding.py` | SentenceTransformer load | CONFIRMED |
| llama-3.3-70b-versatile | LLM | Query understanding, explanation generation, LLM reranking | `app/services/rag.py`, `app/services/query_understanding.py`, `app/services/llm_reranker.py` | Groq API calls | CONFIRMED |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | Reranker | Cross-encoder reranking for search results | `app/services/reranker.py` | CrossEncoder load | CONFIRMED |
| Groq API | External LLM Service | LLM inference (OpenAI-compatible API) | `app/services/rag.py`, etc. | `api.groq.com/openai/v1` | CONFIRMED |
| APScheduler 3.11.0 | Scheduler | Background job scheduling | `app/services/scheduler.py`, `app/services/ingestion_scheduler.py` | BackgroundScheduler | CONFIRMED |
| httpx | HTTP Client | External API calls (Adzuna, Reed) | `app/ingestion/adzuna_source.py`, `app/ingestion/reed_source.py` | Import | CONFIRMED |
| feedparser 6.0.11 | RSS Parser | We Work Remotely RSS feed parsing | `app/ingestion/wwr_scraper.py` | Import | CONFIRMED |
| pandas 2.2.3 | Data Processing | CSV data ingestion | `app/ingestion/csv_source.py`, `app/ingestion/csv_descriptions2.py` | Import | CONFIRMED |
| passlib[bcrypt] 1.7.4 | Auth | Password hashing | `app/core/security.py` | CryptContext(schemes=["bcrypt"]) | CONFIRMED |
| python-jose[cryptography] 3.3.0 | Auth | JWT token creation/verification | `app/core/security.py` | jwt.encode/decode | CONFIRMED |
| Flask-Login 0.6.3 | Auth | Session management for Flask frontend | `webapp/app.py` | LoginManager | CONFIRMED |
| Flask-WTF 1.2.2 | Security | CSRF protection for Flask | `webapp/app.py` | CSRFProtect | CONFIRMED |
| SlowAPI 0.1.9 | Rate Limiting | API rate limiting for FastAPI | `app/main.py` | Limiter | CONFIRMED |
| Flask-Limiter 4.1.1 | Rate Limiting | Rate limiting for Flask routes | `webapp/app.py`, `webapp/routes/auth.py` | Limiter | CONFIRMED |
| smtplib (stdlib) | Email | SMTP email sending | `app/services/email.py` | SMTP, starttls, send_message | CONFIRMED |
| sentence-transformers 3.3.1 | AI Library | Embedding and reranker model loading | `app/services/embedding.py`, `app/services/reranker.py` | SentenceTransformer, CrossEncoder | CONFIRMED |
| torch 2.5.1 | AI Library | Neural network inference backend | `requirements.txt` | Required by sentence-transformers | CONFIRMED |
| openai 1.61.0 | AI Client | Groq API client (OpenAI-compatible) | `app/services/rag.py`, `app/services/llm_reranker.py`, `app/services/query_understanding.py` | OpenAI() client | CONFIRMED |
| rapidfuzz 3.11.0 | Fuzzy Matching | Deduplication and search dedup | `app/processing/dedup.py`, `app/services/search.py` | fuzz.ratio, fuzz.partial_ratio | CONFIRMED |
| numpy 1.26.4 | Numerics | Cosine similarity fallback, array ops | `app/services/vector.py`, `app/services/search.py` | dot product, linalg.norm | CONFIRMED |
| Jinja2 3.1.5 | Templating | HTML template rendering (Flask) | `webapp/templates/` | Template syntax | CONFIRMED |
| pydantic 2.10.5 | Validation | Data validation, settings management | `app/config.py`, all API schemas | BaseSettings, BaseModel | CONFIRMED |
| psycopg2-binary 2.9.10 | DB Driver | PostgreSQL Python adapter | `requirements.txt` | Required by SQLAlchemy | CONFIRMED |
| Docker Compose | Containerization | PostgreSQL container deployment | `docker-compose.yml` | Service definition | CONFIRMED |
| uvicorn 0.34.0 | ASGI Server | FastAPI application server | `app/main.py` | Referenced in startup | CONFIRMED |
| pytest 8.3.4 | Testing | Test framework | `tests/` directory | Test files | CONFIRMED |
| pypdf 5.4.0 | PDF Parsing | Resume PDF text extraction | `app/services/resume_parser.py` | Import | CONFIRMED |

---

# 3. COMPLETE COMPONENT INVENTORY

| ID | Component Name | Purpose | Technology | Input | Output | Dependencies | Evidence |
|----|----------------|---------|------------|-------|--------|--------------|----------|
| C01 | Flask Web UI | User-facing web interface | Flask + Jinja2 | HTTP requests | HTML pages | C02, C03, C04, C08 | `webapp/app.py` |
| C02 | Auth Module (Flask) | User registration, login, password reset | Flask-Login, passlib, python-jose | User credentials | Session/JWT | C08 | `webapp/routes/auth.py` |
| C03 | Main Dashboard (Flask) | Landing page, home feed | Flask | User session | Feed HTML | C04, C08, C17 | `webapp/routes/main.py` |
| C04 | Jobs Module (Flask) | Search, recommendations, job detail, save/unsave | Flask | User requests | HTML/JSON | C08, C09, C10, C11 | `webapp/routes/jobs.py` |
| C05 | Profile Module (Flask) | Profile view/edit, resume upload | Flask | User input | Profile HTML | C08, C12 | `webapp/routes/profile.py` |
| C06 | Admin Module (Flask) | Ingestion runs, job CRUD, aliases, reprocess | Flask | Admin requests | Admin HTML | C08, C09, C13 | `webapp/routes/admin.py` |
| C07 | Admin Guard | Admin role authorization check | Flask decorator | User session | 403/allow | C02 | `webapp/routes/admin_guard.py` |
| C08 | FastAPI REST API | RESTful API server (port 8000) | FastAPI | JSON requests | JSON responses | C09, C10, C11, C14, C15 | `app/main.py` |
| C09 | Database Engine | PostgreSQL connection and ORM | SQLAlchemy + psycopg2 | ORM queries | Query results | PostgreSQL | `app/database.py` |
| C10 | Auth Module (API) | JWT-based authentication | python-jose, passlib, bcrypt | Credentials | JWT token | C09 | `app/api/auth.py` |
| C11 | Users Module (API) | Profile CRUD, notification prefs | FastAPI | Profile updates | Profile data | C09, C12 | `app/api/users.py` |
| C12 | Embedding Service | Text-to-vector embedding generation | sentence-transformers (BAAI/bge-base-en-v1.5) | Text | 768-dim vector | torch | `app/services/embedding.py` |
| C13 | Admin Module (API) | Admin CRUD for jobs, ingestion runs, aliases | FastAPI | Admin requests | JSON | C09 | `app/api/admin.py` |
| C14 | Search Service | 4 search modes + reranking | PostgreSQL, pgvector, cross-encoder, LLM | Search query | Ranked results | C09, C12, C16, C17 | `app/services/search.py` |
| C15 | Recommendation Service | Match scoring (7 weighted signals) | Python | Profile + Job | MatchBreakdown | None (pure computation) | `app/services/recommendation.py` |
| C16 | Reranker Service | Cross-encoder reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 | Query + candidates | Reranked results | torch | `app/services/reranker.py` |
| C17 | LLM Reranker | LLM-based re-scoring | Groq API (llama-3.3-70b-versatile) | Profile text + candidates | Re-scored results | C18 | `app/services/llm_reranker.py` |
| C18 | Groq LLM Client | OpenAI-compatible LLM API client | openai library | Prompts | LLM responses | Groq API | `app/services/rag.py` |
| C19 | RAG Explanation Generator | Match explanation generation | Groq LLM (llama-3.3-70b-versatile) | Profile + Job + Breakdown | ExplanationResult | C18 | `app/services/rag.py` |
| C20 | Explanation Validator | Validates LLM explanations for hallucination | rapidfuzz | Explanation + context | ValidationResult | None (pure computation) | `app/services/explanation_validator.py` |
| C21 | Query Understanding | LLM intent classification + term expansion | Groq LLM | Search query | QueryAnalysis | C18 | `app/services/query_understanding.py` |
| C22 | Recommendation Agent | Full recommendation pipeline with decisions | SQLAlchemy, pgvector, cross-encoder | User profile | Ranked recommendations | C09, C12, C15, C16, C23 | `app/agents/recommendation_agent.py` |
| C23 | Feedback Loop | User interaction-based personalization | Python | Interactions | Score adjustments | C09 | `app/services/feedback_loop.py` |
| C24 | Interaction Tracker | User interaction logging | SQLAlchemy | Interaction events | Stored interactions | C09 | `app/services/interaction_tracker.py` |
| C25 | Notification Agent | Notification candidate generation + email dispatch | SQLAlchemy, email service | New jobs + users | Email digests | C09, C15, C31 | `app/agents/notification_agent.py` |
| C26 | Notification Trigger | Fire-and-forget background notification dispatch | ThreadPoolExecutor | User ID | Background task | C25 | `app/services/notification_trigger.py` |
| C27 | Notification Scheduler | APScheduler-based periodic notification cycles | APScheduler | Timer triggers | Notification cycles | C25 | `app/services/scheduler.py` |
| C28 | Ingestion Scheduler | APScheduler-based periodic data ingestion | APScheduler | Timer triggers | Ingestion cycles | C30 | `app/services/ingestion_scheduler.py` |
| C29 | Processing Pipeline | Raw job → normalised job transformation | Python (7 processing modules) | RawJob records | Job + JobSkill + JobPosting | C12, C33, C34, C35, C36, C37, C38, C39 | `app/processing/pipeline.py` |
| C30 | Ingestion Service | External data source connectors | httpx, feedparser, pandas | External APIs/feeds | RawJob records | C41, C42, C43, C44 | `app/ingestion/base.py` |
| C31 | Email Service | SMTP email sending | smtplib (stdlib) | Email content | Sent email | SMTP server | `app/services/email.py` |
| C32 | Profile Completeness | Profile completeness calculation | Python | UserProfile | CompletenessResult | None (pure computation) | `app/services/profile_completeness.py` |
| C33 | Title Cleaner | Job title noise removal | regex | Raw title | Clean title | None | `app/processing/title.py` |
| C34 | Salary Parser | Salary text parsing and normalisation | regex | Description + raw values | ParsedSalary | None | `app/processing/salary.py` |
| C35 | Location Normaliser | Location text → structured location | regex, lookup tables | Location text + description | Structured location dict | None | `app/processing/location.py` |
| C36 | Category Normaliser | Raw category → canonical category | keyword rules, fuzzy match | Category + title | Canonical category | None | `app/processing/category.py` |
| C37 | Skill Extractor | Skill extraction from job descriptions | Dictionary matching, context classification | Description text | ExtractedSkill list | None | `app/processing/skills.py` |
| C38 | Dedup Service | Exact hash + fuzzy deduplication | SHA-256, rapidfuzz | Job fields | dedup_hash + is_duplicate | None | `app/processing/dedup.py` |
| C39 | Quality Scorer | 0-100 quality scoring (5 dimensions) | Python | Job fields | QualityScore | None | `app/processing/quality.py` |
| C40 | Vector Service | pgvector helpers + numpy fallback | pgvector, numpy | Embedding + query | Similarity results | C09 | `app/services/vector.py` |
| C41 | Adzuna Source | Adzuna API job scraper | httpx | Adzuna API | RawJobRecord list | Adzuna API | `app/ingestion/adzuna_source.py` |
| C42 | Reed Source | Reed.co.uk API job scraper | httpx | Reed API | RawJobRecord list | Reed API | `app/ingestion/reed_source.py` |
| C43 | WWR Scraper | We Work Remotely RSS scraper | feedparser | RSS feed | RawJobRecord list | WWR website | `app/ingestion/wwr_scraper.py` |
| C44 | CSV Source | CSV dataset importer | pandas | CSV files | RawJobRecord list | None | `app/ingestion/csv_source.py`, `app/ingestion/csv_descriptions2.py` |
| C45 | Password Reset Service | Password reset workflow | python-jose, email service | Reset request | Reset email | C18, C31 | `app/services/password_reset.py` |
| C46 | Scoring Config | Versioned scoring weights for ablation | JSON files, dataclasses | Version | ScoringWeights | None | `app/services/scoring_config.py` |
| C47 | Preferences Service | Canonical preference values + validation | Python | User input | Validated prefs | None | `app/services/preferences.py` |
| C48 | Admin Service | Admin CRUD business logic | SQLAlchemy | Admin requests | Operation results | C09, C33, C38 | `app/services/admin.py` |
| C49 | Token Blacklist | JWT revocation tracking | SQLAlchemy | Token JTI | Blacklist status | C09 | `app/models/token_blacklist.py` |

---

# 4. COMPLETE SYSTEM ARCHITECTURE

## Layers Identified (from actual code)

| Layer | Components | Evidence |
|-------|------------|----------|
| User/Client Layer | Browser → Flask Web UI (port 5000) | `run.py` runs Flask on 5000 |
| Presentation Layer | Flask + Jinja2 templates | `webapp/templates/` |
| API Layer | FastAPI REST API (port 8000) | `app/main.py` |
| Application Layer | API route handlers, Flask route handlers | `app/api/`, `webapp/routes/` |
| AI/ML Layer | Embedding service, LLM services, reranker, query understanding | `app/services/embedding.py`, `app/services/rag.py`, etc. |
| Agent Layer | RecommendationAgent, NotificationAgent | `app/agents/` |
| Processing Layer | Pipeline (7 modules), Skill extraction, Salary parsing, etc. | `app/processing/` |
| Data Layer | PostgreSQL + pgvector | `app/database.py`, `docker-compose.yml` |
| Ingestion Layer | 4 data source connectors | `app/ingestion/` |
| Notification Layer | Email service, Notification scheduler, Trigger | `app/services/email.py`, `app/services/scheduler.py` |
| Infrastructure Layer | Docker (PostgreSQL), APScheduler | `docker-compose.yml` |

| Component | Layer | Technology | Responsibility | Communicates With | Communication Method | Evidence |
|-----------|-------|------------|----------------|-------------------|----------------------|----------|
| Flask Web UI | Presentation | Flask + Jinja2 | Serve HTML pages, form handling | FastAPI (optional) | HTTP (port 5000) | `run.py` |
| FastAPI REST API | API | FastAPI | RESTful JSON API | All backend services | HTTP (port 8000) | `app/main.py` |
| Auth Module (Flask) | Application | Flask-Login, passlib | User session management | Database | ORM queries | `webapp/routes/auth.py` |
| Auth Module (API) | Application | python-jose, passlib | JWT authentication | Database, Token Blacklist | ORM queries | `app/api/auth.py` |
| Admin Guard | Application | Flask decorator | Admin role check | Auth module | Direct function call | `webapp/routes/admin_guard.py` |
| Recommendation Agent | Agent | Python, pgvector, cross-encoder | Full recommendation pipeline | Database, Embedding, Scoring, Reranker, FeedbackLoop | Direct function calls | `app/agents/recommendation_agent.py` |
| Notification Agent | Agent | Python, SQLAlchemy | Notification candidate generation | Database, Email, Scoring | Direct function calls | `app/agents/notification_agent.py` |
| Embedding Service | AI/ML | sentence-transformers (BGE) | Text → 768-dim vector | None (local model) | Function call | `app/services/embedding.py` |
| LLM Client | AI/ML | openai (Groq API) | LLM inference | Groq API (external) | HTTPS REST | `app/services/rag.py` |
| Reranker | AI/ML | cross-encoder/ms-marco-MiniLM | Cross-encoder reranking | None (local model) | Function call | `app/services/reranker.py` |
| Search Service | Application | PostgreSQL, pgvector, rapidfuzz | 4 search modes | Database, Embedding, Reranker, LLM | ORM + function calls | `app/services/search.py` |
| Recommendation Service | Application | Python | Match scoring (7 signals) | None (pure computation) | Function call | `app/services/recommendation.py` |
| Processing Pipeline | Processing | 7 Python modules | Raw → normalised job | Embedding, 7 processing modules | Function calls | `app/processing/pipeline.py` |
| Ingestion Service | Ingestion | httpx, feedparser, pandas | Fetch from external sources | Adzuna, Reed, WWR, CSV | HTTP/RSS/File | `app/ingestion/base.py` |
| Database | Data | PostgreSQL 16 + pgvector | Persistent storage + vector search | All ORM components | SQLAlchemy ORM | `app/database.py` |
| Email Service | Notification | smtplib | SMTP email delivery | SMTP server (Gmail) | SMTP/TLS | `app/services/email.py` |
| Notification Scheduler | Notification | APScheduler | Periodic notification triggers | Notification Agent | Function call | `app/services/scheduler.py` |
| Ingestion Scheduler | Infrastructure | APScheduler | Periodic data ingestion triggers | Ingestion Service, Processing Pipeline | Function call | `app/services/ingestion_scheduler.py` |
| Docker Compose | Infrastructure | Docker | PostgreSQL container | Host system | TCP port 5432 | `docker-compose.yml` |

---

# 5. ARCHITECTURE RELATIONSHIPS

| Source | Destination | Direction | Data Exchanged | Communication | Purpose | Evidence |
|--------|-------------|-----------|----------------|---------------|---------|----------|
| User Browser | Flask Web UI | → | HTTP requests | HTTP (port 5000) | Web interface access | `run.py` |
| Flask Web UI | FastAPI API | → | JSON API calls | HTTP (port 8000) | Data retrieval (optional) | CORS config in `app/main.py` |
| Flask Web UI | Database | → | ORM queries | SQLAlchemy | Data read/write | `webapp/app.py` imports SessionLocal |
| FastAPI API | Database | → | ORM queries | SQLAlchemy | Data read/write | `app/database.py` |
| FastAPI API | Embedding Service | → | Text input | Function call | Generate embeddings | `app/api/users.py`, `app/api/jobs.py` |
| FastAPI API | Search Service | → | Search queries | Function call | Job search | `app/api/jobs.py` |
| FastAPI API | Recommendation Agent | → | Profile data | Function call | Generate recommendations | `app/api/recommendations.py` |
| FastAPI API | RAG Explanation | → | Profile + Job + Breakdown | Function call | Generate explanations | `app/api/recommendations.py` |
| FastAPI API | Query Understanding | → | Search query | Function call | Query expansion | `app/services/search.py` |
| Recommendation Agent | Database | → | Queries + inserts | SQLAlchemy | Read jobs, write recommendations | `app/agents/recommendation_agent.py` |
| Recommendation Agent | Embedding Service | → | Profile text | Function call | Compute profile embedding | `app/agents/recommendation_agent.py` |
| Recommendation Agent | Scoring Service | → | Profile + Job + Skills | Function call | Match scoring | `app/agents/recommendation_agent.py` |
| Recommendation Agent | Reranker | → | Query + candidates | Function call | Cross-encoder reranking | `app/agents/recommendation_agent.py` |
| Recommendation Agent | Feedback Loop | → | User ID | Function call | Interaction adjustments | `app/agents/recommendation_agent.py` |
| Recommendation Agent | Notification Trigger | → | User ID | Function call (async) | Trigger notifications | `app/agents/recommendation_agent.py` |
| Notification Agent | Database | → | Queries | SQLAlchemy | Read new jobs, users, prefs | `app/agents/notification_agent.py` |
| Notification Agent | Email Service | → | Email content | Function call | Send digest email | `app/agents/notification_agent.py` |
| Notification Agent | Scoring Service | → | Profile + Job | Function call | Compute match scores | `app/agents/notification_agent.py` |
| Notification Scheduler | Notification Agent | → | frequency param | Function call | Trigger notification cycle | `app/services/scheduler.py` |
| Ingestion Scheduler | Ingestion Service | → | Source config | Function call | Trigger data fetch | `app/services/ingestion_scheduler.py` |
| Ingestion Scheduler | Processing Pipeline | → | Raw jobs | Function call | Trigger processing | `app/services/ingestion_scheduler.py` |
| Ingestion Service | Adzuna API | → | API request | HTTPS GET | Fetch jobs | `app/ingestion/adzuna_source.py` |
| Ingestion Service | Reed API | → | API request | HTTPS GET (Basic Auth) | Fetch jobs | `app/ingestion/reed_source.py` |
| Ingestion Service | WWR RSS | → | RSS request | HTTP GET | Fetch jobs | `app/ingestion/wwr_scraper.py` |
| Ingestion Service | CSV Files | → | File read | File I/O | Import jobs | `app/ingestion/csv_source.py` |
| Processing Pipeline | Embedding Service | → | Job text | Function call | Generate job embedding | `app/processing/pipeline.py` |
| Processing Pipeline | Title Cleaner | → | Raw title | Function call | Clean title | `app/processing/pipeline.py` |
| Processing Pipeline | Salary Parser | → | Description + raw salary | Function call | Parse salary | `app/processing/pipeline.py` |
| Processing Pipeline | Location Normaliser | → | Location text | Function call | Normalise location | `app/processing/pipeline.py` |
| Processing Pipeline | Category Normaliser | → | Category + title | Function call | Normalise category | `app/processing/pipeline.py` |
| Processing Pipeline | Skill Extractor | → | Description text | Function call | Extract skills | `app/processing/pipeline.py` |
| Processing Pipeline | Dedup Service | → | Job fields | Function call | Generate dedup hash | `app/processing/pipeline.py` |
| Processing Pipeline | Quality Scorer | → | Job fields | Function call | Score quality | `app/processing/pipeline.py` |
| Email Service | SMTP Server (Gmail) | → | Email message | SMTP/TLS (port 587) | Deliver email | `app/services/email.py` |
| LLM Client | Groq API | → | Chat completion request | HTTPS REST | LLM inference | `app/services/rag.py` |
| Search Service | Database | → | SQL queries | SQLAlchemy | Full-text + vector search | `app/services/search.py` |
| Search Service | Embedding Service | → | Query text | Function call | Query embedding | `app/services/search.py` |
| Search Service | Reranker | → | Query + results | Function call | Cross-encoder rerank | `app/services/search.py` |
| Search Service | LLM Reranker | → | Profile + results | Function call | LLM re-scoring | `app/services/search.py` |

---

# 6. ARCHITECTURE BOUNDARIES

| Boundary | Components Inside | Components Outside | Communication Across Boundary |
|----------|-------------------|---------------------|-------------------------------|
| Client-Server | Browser | Flask Web UI, FastAPI API | HTTP requests/responses |
| Flask-FastAPI | Flask routes | FastAPI routes | HTTP (port 8000), shared DB |
| Server-Database | All application services | PostgreSQL + pgvector | SQLAlchemy ORM, raw SQL with pgvector ops |
| Server-External APIs | Ingestion Service | Adzuna API, Reed API, WWR RSS, Groq API, SMTP | HTTPS, HTTP, SMTP/TLS |
| Server-Local ML | Embedding Service, Reranker | None (runs in-process) | Function calls |
| Background Processing | Scheduler, ThreadPoolExecutor | Application services | Function calls (same process) |
| Authentication Boundary | Protected routes | Unauthenticated access | JWT token / Flask-Login session |
| Admin Boundary | Admin routes | Regular user routes | is_admin check |

---

# 7. COMPLETE SYSTEM WORKFLOW

## A. Data Ingestion & Processing Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| F01 | Ingestion Scheduler | Trigger ingestion | Timer (6h WWR, daily processing) | APScheduler fires job | Ingestion command | F02 | `app/services/ingestion_scheduler.py` |
| F02 | AdzunaSource/ReedSource/WWRScraper/CsvSource | Fetch raw jobs | API credentials / RSS URL / CSV path | HTTP GET, RSS parse, CSV read | RawJobRecord list | F03 | `app/ingestion/*.py` |
| F03 | Database | Store raw jobs | RawJobRecord | INSERT INTO raw_jobs | RawJob records | F04 | `app/ingestion/base.py` |
| F04 | Processing Pipeline | Process raw jobs | RawJob records | Per-job processing (steps F05-F15) | Job + JobSkill + JobPosting | F16 | `app/processing/pipeline.py` |
| F05 | Title Cleaner | Clean title | Raw title string | Regex noise removal, title case | Clean title | F06 | `app/processing/title.py` |
| F06 | Salary Parser | Parse salary | Description + raw salary values | Regex extraction, period detection, normalisation | ParsedSalary | F07 | `app/processing/salary.py` |
| F07 | Location Normaliser | Normalise location | Location text + description | Keyword detection, country alias, UK-specific parsing | Structured location dict | F08 | `app/processing/location.py` |
| F08 | Category Normaliser | Normalise category | Raw category + title | Keyword rules, fuzzy matching | Canonical category | F09 | `app/processing/category.py` |
| F09 | Skill Extractor | Extract skills | Job description text | Dictionary matching, context classification | Skill list | F10 | `app/processing/skills.py` |
| F10 | Dedup Service | Generate dedup hash | Title + company + location + salary | SHA-256 hash | dedup_hash | F11 | `app/processing/dedup.py` |
| F11 | Dedup Service | Check duplicate | dedup_hash | DB lookup for existing hash | Skip if exists | F12 | `app/processing/pipeline.py` |
| F12 | Embedding Service | Generate embedding | Job text (title×2 + description + skills + location) | BGE model inference | 768-dim vector | F13 | `app/services/embedding.py` |
| F13 | Quality Scorer | Score quality | Job fields | 5-dimension weighted scoring | QualityScore (0-100) | F14 | `app/processing/quality.py` |
| F14 | Database | Store job | Processed job data | INSERT INTO jobs + job_skills + job_postings | Job record | F15 | `app/processing/pipeline.py` |
| F15 | Database | Store posting | Raw job → canonical job link | UPSERT INTO job_postings | JobPosting record | F16 | `app/processing/pipeline.py` |
| F16 | Processing Pipeline | Log errors | Any failure in F05-F15 | INSERT INTO processing_errors | ProcessingError record | End | `app/processing/pipeline.py` |

## B. User Registration & Profile Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| U01 | Auth Module | Register user | Email + password + name | Validate password, hash, INSERT user + profile + notif prefs | User account | U02 | `app/api/auth.py` |
| U02 | Auth Module | Login | Email + password | Verify credentials, check blacklist, create JWT | JWT token | U03 | `app/api/auth.py` |
| U03 | Users Module | Update profile | Profile fields | Validate, normalise skills, generate embedding | Updated profile | U04 | `app/api/users.py` |
| U04 | Embedding Service | Generate profile embedding | Profile text (headline×2 + skills + interests + experience) | BGE model inference | 768-dim vector → profile_embedding | End | `app/services/embedding.py` |

## C. Search Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| S01 | Search Service | Receive query | Search query + params | Route to appropriate search mode | — | S02 | `app/services/search.py` |
| S02 | Query Understanding | Analyse query | Query text | LLM intent classification + expansion | QueryAnalysis (expanded_terms) | S03 | `app/services/query_understanding.py` |
| S03 | Search Service | Determine query type | Query text | Check TECH_ALIASES, skill dictionary, token count | is_technical (bool) | S04 | `app/services/search.py` |
| S04a | Search Service | Evidence search (technical) | Query + expanded terms | Lexical evidence retrieval + semantic fallback | SearchResults | S05 | `app/services/search.py` |
| S04b | Search Service | Semantic search (non-technical) | Query | pgvector cosine similarity | SearchResults | S05 | `app/services/search.py` |
| S04c | Search Service | Hybrid search | Query + filters | Semantic + SQL filters | SearchResults | S05 | `app/services/search.py` |
| S05 | Reranker | Cross-encoder rerank (optional) | Query + results | Cross-encoder scoring, 0.7+0.3 blend | Reranked results | S06 | `app/services/reranker.py` |
| S06 | LLM Reranker | LLM re-scoring (optional) | Profile text + results | Groq LLM scoring, 0.4 blend | Re-scored results | End | `app/services/llm_reranker.py` |

## D. Recommendation Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| R01 | Recommendation Agent | Start pipeline | User profile | Check skills/headline exist | — | R02 | `app/agents/recommendation_agent.py` |
| R02 | Embedding Service | Compute profile embedding | Profile text | BGE model (if missing) | 768-dim vector | R03 | `app/agents/recommendation_agent.py` |
| R03 | Database | Retrieve candidates | Profile embedding | pgvector cosine distance (top 30) | Candidate jobs | R04 | `app/agents/recommendation_agent.py` |
| R04 | Scoring Service | Score candidates | Profile + candidates + skills | 7-signal weighted scoring | Scored candidates | R05 | `app/services/recommendation.py` |
| R05 | Recommendation Agent | Expand pool? | Average score | If avg < 0.35, expand to 80 | More candidates | R06 | `app/agents/recommendation_agent.py` |
| R06 | Recommendation Agent | Filter | Hard constraints + min score | Remove below threshold | Filtered candidates | R07 | `app/agents/recommendation_agent.py` |
| R07 | Recommendation Agent | Collapse duplicates | Scored list | rapidfuzz dedup | Deduplicated list | R08 | `app/agents/recommendation_agent.py` |
| R08 | Reranker | Cross-encoder rerank | Scored list | If pool > 20, blend 0.7+0.3 | Reranked list | R09 | `app/agents/recommendation_agent.py` |
| R09 | Database | Persist recommendations | Top N scored | DELETE old + INSERT new | Recommendation records | R10 | `app/agents/recommendation_agent.py` |
| R10 | Notification Trigger | Dispatch async | User ID | ThreadPoolExecutor fire-and-forget | Background check | End | `app/agents/recommendation_agent.py` |

## E. Notification Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| N01 | Scheduler/Trigger | Start cycle | Timer or user action | APScheduler or ThreadPoolExecutor | Cycle start | N02 | `app/services/scheduler.py` |
| N02 | Notification Agent | Get new jobs | Since timestamp | SELECT jobs WHERE created_at > since | New job list | N03 | `app/agents/notification_agent.py` |
| N03 | Notification Agent | Get active users | Frequency filter | SELECT users WHERE notifications enabled | User list | N04 | `app/agents/notification_agent.py` |
| N04 | Notification Agent | Process per user | User + new jobs | Generate candidates from 3 sources | Candidate list | N05 | `app/agents/notification_agent.py` |
| N05 | Scoring Service | Score candidates | Profile + jobs | Match scoring for each candidate | Scored candidates | N06 | `app/agents/notification_agent.py` |
| N06 | Notification Agent | Filter + deduplicate | Scored candidates | Min score threshold, dedupe_key check | Final candidates | N07 | `app/agents/notification_agent.py` |
| N07 | Email Service | Send digest | Email content | SMTP send | Email delivered | N08 | `app/services/email.py` |
| N08 | Database | Record notification | Notification data | INSERT INTO notifications | Notification record | End | `app/agents/notification_agent.py` |

## F. Explanation Generation Flow

| Step ID | Component | Action | Input | Processing | Output | Next Step | Evidence |
|---------|-----------|--------|-------|------------|--------|-----------|----------|
| E01 | RAG Generator | Build evidence | Profile + Job + Breakdown | Construct evidence block text | Evidence text | E02 | `app/services/rag.py` |
| E02 | RAG Generator | Select prompt | Match tier (high/medium/low) | Tier-based prompt selection | System + user prompts | E03 | `app/services/rag.py` |
| E03 | LLM Client | Generate explanation | Prompts | Groq API call (llama-3.3-70b-versatile) | Raw LLM text | E04 | `app/services/rag.py` |
| E04 | RAG Generator | Parse response | Raw text | Structured parsing | ExplanationResult | E05 | `app/services/rag.py` |
| E05 | Explanation Validator | Validate | Explanation + context | Skill/salary/location/experience checks | ValidationResult | End | `app/services/explanation_validator.py` |

---

# 8. DATA PROCESSING PIPELINE

| Stage | Input | Operation | Technology | Output | Storage | Evidence |
|-------|-------|-----------|------------|--------|---------|----------|
| Data Source | External APIs/feeds/files | Fetch raw job data | httpx, feedparser, pandas | RawJobRecord | None (in-memory) | `app/ingestion/` |
| Raw Storage | RawJobRecord | Store raw payload | SQLAlchemy | raw_jobs table | PostgreSQL | `app/ingestion/base.py` |
| Title Cleaning | Raw title | Regex noise removal | Python regex | Clean title | In-memory | `app/processing/title.py` |
| Salary Parsing | Description + raw values | Regex extraction + normalisation | Python regex | ParsedSalary | In-memory | `app/processing/salary.py` |
| Location Normalisation | Location text + description | Keyword detection, alias resolution | Python regex + lookup dicts | Structured location | In-memory | `app/processing/location.py` |
| Category Normalisation | Raw category + title | Keyword rules + fuzzy matching | Python | Canonical category | In-memory | `app/processing/category.py` |
| Skill Extraction | Job description | Dictionary matching + context classification | Python dict + keywords | Skill list | In-memory | `app/processing/skills.py` |
| Dedup Hashing | Title + company + location + salary | SHA-256 hash | hashlib | dedup_hash | In-memory | `app/processing/dedup.py` |
| Dedup Check | dedup_hash | DB lookup | SQLAlchemy | Skip if exists | PostgreSQL | `app/processing/pipeline.py` |
| Embedding | Job text (title×2 + desc + skills + location) | BGE model inference | sentence-transformers | 768-dim vector | In-memory | `app/services/embedding.py` |
| Quality Scoring | Job fields | 5-dimension weighted scoring | Python | QualityScore (0-100) | In-memory | `app/processing/quality.py` |
| Job Storage | All processed fields | INSERT job + skills + posting | SQLAlchemy | jobs, job_skills, job_postings | PostgreSQL | `app/processing/pipeline.py` |
| Skill Storage | Extracted skills | INSERT per skill | SQLAlchemy | job_skills | PostgreSQL | `app/processing/pipeline.py` |
| Posting Linking | Canonical job + raw job | UPSERT posting | SQLAlchemy | job_postings | PostgreSQL | `app/processing/pipeline.py` |
| Error Logging | Any failure | INSERT error record | SQLAlchemy | processing_errors | PostgreSQL | `app/processing/pipeline.py` |

---

# 9. DECISION POINTS

| Decision ID | Decision | Condition | TRUE Path | FALSE Path | Evidence |
|-------------|----------|-----------|-----------|------------|----------|
| D01 | User authenticated? | JWT valid + not blacklisted + user active | Allow request | HTTP 401 | `app/core/deps.py` |
| D02 | User is admin? | user.is_admin == True | Allow admin route | HTTP 403 | `app/core/deps.py`, `webapp/routes/admin_guard.py` |
| D03 | Password valid? | Meets complexity requirements | Proceed with registration | HTTP 422 | `app/services/password_reset.py` |
| D04 | Email already registered? | Email exists in users table | HTTP 409 | Create user | `app/api/auth.py` |
| D05 | Credentials correct? | Email found + password verify | Issue JWT | HTTP 401 | `app/api/auth.py` |
| D06 | User active? | user.is_active == True | Allow login | HTTP 403 | `app/api/auth.py` |
| D07 | Profile exists? | UserProfile row found | Return profile | HTTP 404 | `app/api/users.py` |
| D08 | Skills/headline present? | profile.skills or profile.headline non-empty | Generate recommendations | HTTP 400 | `app/api/recommendations.py` |
| D09 | Query is technical? | Length ≤ 3, in TECH_ALIASES, or in skill dict | Evidence search path | Semantic search path | `app/services/search.py` |
| D10 | Enough lexical results? | len(results) >= EVIDENCE_MIN_RESULTS (5) | Return lexical results | Semantic fallback | `app/services/search.py` |
| D11 | Job already exists? | dedup_hash matches existing | Skip insertion | Insert new job | `app/processing/pipeline.py` |
| D12 | Raw job already processed? | raw_job_id has existing Job record | Update existing | Insert new | `app/processing/pipeline.py` |
| D13 | Candidate pool score low? | avg_score < 0.35 | Expand pool to 80 | Keep at 30 | `app/agents/recommendation_agent.py` |
| D14 | Pool large enough for rerank? | Pool > 20 candidates | Apply cross-encoder rerank | Skip reranking | `app/agents/recommendation_agent.py` |
| D15 | SMTP configured? | smtp_user and smtp_password set | Send email | Log and skip | `app/services/email.py` |
| D16 | Scheduler enabled? | settings.scheduler_enabled == True | Start scheduler | Skip | `app/main.py` |
| D17 | Notification required? | New jobs meet min_match_score threshold | Queue notification | Skip | `app/agents/notification_agent.py` |
| D18 | Reranker available? | CrossEncoder model loaded | Apply reranking | Skip | `app/services/reranker.py` |
| D19 | Profile has embedding? | profile.profile_embedding is not None | Use for cosine similarity | Default to 0.5 | `app/api/recommendations.py` |
| D20 | Match tier? | overall_score >= 0.75 (high), >= 0.45 (medium), else low | Select tier-specific prompt | Default prompt | `app/services/rag.py` |
| D21 | LLM explanation valid? | ValidationResult.is_valid == True | Use explanation | Retry/fallback | `app/services/rag.py` |
| D22 | Is UK location? | Country in (uk, gb) | Run UK-specific parsing | Standard parsing | `app/processing/location.py` |
| D23 | Is remote job? | Location text in REMOTE_KEYWORDS | Set remote=True, workplace_type="remote" | Check hybrid/onsite | `app/processing/location.py` |
| D24 | Alias exists? | NormalizationAlias found in DB | Use canonical value | Use original value | `app/processing/pipeline.py` |
| D25 | Failed only mode? | request.failed_only == True | Filter processing_errors | Process all | `app/services/admin.py` |

---

# 10. ERROR/FAILURE PATHS

| Failure | Trigger | System Response | Recovery/Fallback | Evidence |
|---------|---------|-----------------|-------------------|----------|
| Ingestion API failure | HTTP error / timeout | retry_with_backoff (3 retries, exponential backoff) | Skip page, log error | `app/ingestion/base.py` |
| Ingestion API auth failure | Invalid API key | ValueError raised | Stop ingestion for that source | `app/ingestion/adzuna_source.py`, `reed_source.py` |
| RSS parse failure | feedparser error | retry_with_backoff (3 retries) | Log and skip | `app/ingestion/wwr_scraper.py` |
| CSV file not found | Missing file | FileNotFoundError | Stop CSV ingestion | `app/ingestion/csv_source.py` |
| Salary parse failure | Unparseable salary text | ParsedSalary with confidence=0.0 | Store as NULL | `app/processing/salary.py` |
| Embedding generation failure | Model error | ProcessingError logged, raw_job marked unprocessed | Skip embedding | `app/processing/pipeline.py` |
| Duplicate job detected | dedup_hash match | Skip insertion, increment raw_jobs.processing_attempts | — | `app/processing/pipeline.py` |
| LLM API failure | Groq API error | Fallback to template-based explanation | Retry (max 2), then fallback text | `app/services/rag.py` |
| LLM reranker failure | Groq API error | Skip LLM reranking, use original scores | Log debug | `app/services/llm_reranker.py` |
| Query understanding failure | Groq API error | Use basic analysis (no expansion) | Log debug | `app/services/query_understanding.py` |
| Cross-encoder unavailable | Model not loaded | Skip reranking, use original scores | Check is_reranker_available() | `app/services/reranker.py` |
| SMTP not configured | Missing credentials | Log info, return False | Skip email delivery | `app/services/email.py` |
| SMTP send failure | Connection / auth error | Log exception, return False | Skip email | `app/services/email.py` |
| Notification failure | Email send failure | Log failure, record in notifications table | Retry up to NOTIFICATION_MAX_RETRIES (3) | `app/agents/notification_agent.py` |
| JWT token blacklisted | Token JTI in blacklist | HTTP 401 | User must re-authenticate | `app/core/deps.py` |
| Database connection failure | Connection error | SQLAlchemy raises | App crashes (no retry logic evidenced) | — |
| pgvector not available | Extension not installed | init_db() runs CREATE EXTENSION | App fails to start | `app/database.py` |
| Location parse ambiguity | Unknown location format | Return partial result (city=None, country=None) | Still process job | `app/processing/location.py` |
| Skill extraction low confidence | No dictionary match | confidence=0.1, classification="required" | Still include skill | `app/processing/skills.py` |
| Rate limit exceeded | Too many requests | SlowAPI / Flask-Limiter returns 429 | Client must wait | `app/main.py`, `webapp/app.py` |
| Admin reprocess without confirmation | confirmed=False | HTTP 400 | Require confirmation | `app/api/admin.py` |
| Resume PDF parse failure | Invalid PDF | pypdf error | Return empty text | `app/services/resume_parser.py` |

---

# 11. DATABASE TECHNOLOGY

| Item | Value | Evidence | Confidence |
|------|-------|----------|------------|
| DBMS | PostgreSQL 16 | `docker-compose.yml` image: pgvector/pgvector:pg16 | CONFIRMED |
| Vector Extension | pgvector | `CREATE EXTENSION IF NOT EXISTS vector` | CONFIRMED |
| ORM | SQLAlchemy 2.0.36 | All model files, `app/database.py` | CONFIRMED |
| Migration Tool | Alembic 1.14.1 | `alembic/` directory, 7 migrations | CONFIRMED |
| DB Driver | psycopg2-binary 2.9.10 | `requirements.txt` | CONFIRMED |
| Container | Docker Compose | `docker-compose.yml` | CONFIRMED |
| Database Name | jobmatch | `docker-compose.yml`, `.env` | CONFIRMED |
| Vector Dimensions | 768 | `Vector(768)` in models, `app/config.py` | CONFIRMED |
| Vector Index | HNSW (m=16, ef_construction=64) | Migration 003 | CONFIRMED |
| Full-Text Search | PostgreSQL TSVECTOR | Computed column + GIN index | CONFIRMED |

---

# 12. COMPLETE ENTITY/SCHEMA INVENTORY

## 12.1 Users Domain

### Table: `users`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | User identifier | `app/models/user.py` |
| email | VARCHAR(255) | UNIQUE, INDEX | NO | User email | `app/models/user.py` |
| password_hash | VARCHAR(255) | | NO | Bcrypt password hash | `app/models/user.py` |
| is_active | BOOLEAN | | YES (default True) | Account active flag | `app/models/user.py` |
| is_admin | BOOLEAN | | NO (default False) | Admin role flag | Migration 005 |
| created_at | DATETIME | | YES (default now()) | Registration timestamp | `app/models/user.py` |

### Table: `user_profiles`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Profile identifier | `app/models/user.py` |
| user_id | UUID | FK→users.id (CASCADE), UNIQUE | NO | Linked user | `app/models/user.py` |
| full_name | VARCHAR(255) | | YES | User's full name | `app/models/user.py` |
| headline | VARCHAR(500) | | YES | Professional headline | `app/models/user.py` |
| skills | ARRAY(String) | | YES | User's skills list | `app/models/user.py` |
| experience_years | INTEGER | | YES | Years of experience | `app/models/user.py` |
| experience_level | VARCHAR(50) | | YES | junior/mid/senior | `app/models/user.py` |
| preferred_locations | ARRAY(String) | | YES | Location preferences | `app/models/user.py` |
| preferred_job_types | ARRAY(String) | | YES | Job type preferences | `app/models/user.py` |
| min_salary | FLOAT | | YES | Minimum salary expectation | `app/models/user.py` |
| salary_currency | VARCHAR(10) | | YES (default "USD") | Salary currency | `app/models/user.py` |
| career_interests | TEXT | | YES | Career interests text | `app/models/user.py` |
| profile_embedding | Vector(768) | | YES | Profile embedding vector | `app/models/user.py` |

### Table: `notification_preferences`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Preference identifier | `app/models/user.py` |
| user_id | UUID | FK→users.id (CASCADE), UNIQUE | NO | Linked user | `app/models/user.py` |
| email_enabled | BOOLEAN | | YES (default True) | Email notifications on/off | `app/models/user.py` |
| min_match_score | FLOAT | | YES (default 0.70) | Min score threshold | `app/models/user.py` |
| frequency | VARCHAR(20) | CHECK (instant/daily/weekly) | YES (default "daily") | Notification frequency | `app/models/user.py`, Migration 006 |
| timezone | VARCHAR(50) | NOT NULL (default "UTC") | NO | User timezone | Migration 006 |
| last_processed_at | DATETIME | | YES | Last notification processing time | Migration 006 |
| last_digest_sent_at | DATETIME | | YES | Last digest sent time | Migration 006 |

## 12.2 Jobs Domain

### Table: `raw_jobs`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Raw job identifier | `app/models/job.py` |
| source | VARCHAR(50) | | NO | Data source (csv/adzuna/wwr/reed) | `app/models/job.py` |
| source_job_id | VARCHAR(255) | | YES | Original source ID | `app/models/job.py` |
| payload | JSONB | | NO | Raw data payload | `app/models/job.py` |
| fetched_at | DATETIME | | YES (default now()) | Fetch timestamp | `app/models/job.py` |
| processed | BOOLEAN | INDEX | YES (default False) | Processing status | `app/models/job.py` |
| ingestion_run_id | UUID | FK→ingestion_runs.id (SET NULL), INDEX | YES | Linked ingestion run | Migration 005 |
| processing_attempts | INTEGER | NOT NULL (default 0) | NO | Attempt counter | Migration 005 |

**Unique Index:** (source, source_job_id)

### Table: `jobs`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Job identifier | `app/models/job.py` |
| raw_job_id | UUID | FK→raw_jobs.id | YES | Source raw record | `app/models/job.py` |
| title | VARCHAR(500) | NOT NULL | NO | Original title | `app/models/job.py` |
| title_clean | VARCHAR(500) | | YES | Cleaned title | `app/models/job.py` |
| company | VARCHAR(255) | | YES | Company name | `app/models/job.py` |
| description | TEXT | | YES | Job description | `app/models/job.py` |
| description_clean | TEXT | | YES | Cleaned description | `app/models/job.py` |
| requirements | TEXT | | YES | Job requirements | `app/models/job.py` |
| responsibilities | TEXT | | YES | Job responsibilities | `app/models/job.py` |
| location_city | VARCHAR(255) | | YES | City | `app/models/job.py` |
| location_country | VARCHAR(100) | | YES | Country | `app/models/job.py` |
| remote | BOOLEAN | | YES (default False) | Remote flag | `app/models/job.py` |
| uk_country | VARCHAR(50) | | YES | UK country | `app/models/job.py` |
| uk_region | VARCHAR(100) | | YES | UK region | `app/models/job.py` |
| county | VARCHAR(100) | | YES | UK county | `app/models/job.py` |
| postcode_area | VARCHAR(10) | | YES | UK postcode area | `app/models/job.py` |
| latitude | FLOAT | | YES | GPS latitude | `app/models/job.py` |
| longitude | FLOAT | | YES | GPS longitude | `app/models/job.py` |
| workplace_type | VARCHAR(50) | | YES | remote/hybrid/onsite | `app/models/job.py` |
| salary_min | FLOAT | | YES | Minimum salary | `app/models/job.py` |
| salary_max | FLOAT | | YES | Maximum salary | `app/models/job.py` |
| salary_currency | VARCHAR(10) | | YES | Salary currency | `app/models/job.py` |
| salary_period | VARCHAR(20) | | YES | annual/monthly/hourly/daily | `app/models/job.py` |
| original_salary_text | VARCHAR(255) | | YES | Original salary text | `app/models/job.py` |
| annualised_gbp_salary | FLOAT | | YES | Annualised GBP salary | `app/models/job.py` |
| salary_confidence | FLOAT | | YES | Parsing confidence (0-1) | `app/models/job.py` |
| category | VARCHAR(100) | INDEX | YES | Canonical category | `app/models/job.py` |
| job_type | VARCHAR(50) | | YES | full-time/part-time/contract | `app/models/job.py` |
| contract_duration | VARCHAR(50) | | YES | Contract duration | `app/models/job.py` |
| experience_level | VARCHAR(50) | | YES | Experience level | `app/models/job.py` |
| posted_at | DATETIME | | YES | Posting date | `app/models/job.py` |
| closing_date | DATETIME | | YES | Closing date | `app/models/job.py` |
| url | VARCHAR(1000) | | YES | Application URL | `app/models/job.py` |
| source | VARCHAR(50) | NOT NULL | NO | Data source | `app/models/job.py` |
| dedup_hash | VARCHAR(64) | UNIQUE, INDEX | YES | Deduplication hash | `app/models/job.py` |
| is_active | BOOLEAN | INDEX | YES (default True) | Active flag | `app/models/job.py` |
| quality_score | FLOAT | | YES | Quality score (0-100) | `app/models/job.py` |
| search_vector | TSVECTOR | COMPUTED, GIN INDEX | YES | Full-text search vector | Migration 003 |
| embedding | Vector(768) | HNSW INDEX | YES | Job embedding vector | `app/models/job.py` |
| embedding_model | VARCHAR(100) | | YES | Model used | `app/models/job.py` |
| embedding_dim | INTEGER | | YES | Embedding dimensions | `app/models/job.py` |
| embedded_at | DATETIME | | YES | Embedding timestamp | `app/models/job.py` |
| source_text_hash | VARCHAR(64) | | YES | Source text hash | `app/models/job.py` |
| processing_version | VARCHAR(50) | | YES | Pipeline version | `app/models/job.py` |
| created_at | DATETIME | INDEX | YES (default now()) | Creation timestamp | `app/models/job.py` |
| updated_at | DATETIME | | YES (onupdate) | Last update timestamp | `app/models/job.py` |

**Check constraint:** `salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max` (Migration 005)

### Table: `job_skills`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Skill identifier | `app/models/job.py` |
| job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Linked job | `app/models/job.py` |
| skill | TEXT | NOT NULL | NO | Skill name | `app/models/job.py` |
| confidence | FLOAT | | YES | Extraction confidence | `app/models/job.py` |
| is_essential | BOOLEAN | | YES | Essential flag | `app/models/job.py` |
| extraction_method | VARCHAR(50) | | YES | dictionary/llm/hybrid | `app/models/job.py` |

**Unique Index:** (job_id, skill)

### Table: `job_postings`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Posting identifier | `app/models/job_posting.py` |
| canonical_job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Canonical job | `app/models/job_posting.py` |
| raw_job_id | UUID | FK→raw_jobs.id (SET NULL) | YES | Source raw record | `app/models/job_posting.py` |
| source | VARCHAR(50) | NOT NULL | NO | Data source | `app/models/job_posting.py` |
| source_job_id | VARCHAR(255) | | YES | Source-specific ID | `app/models/job_posting.py` |
| source_url | VARCHAR(1000) | | YES | Original URL | `app/models/job_posting.py` |
| original_title | VARCHAR(500) | | YES | Original title | `app/models/job_posting.py` |
| original_description | TEXT | | YES | Original description | `app/models/job_posting.py` |
| original_location | VARCHAR(500) | | YES | Original location text | `app/models/job_posting.py` |
| original_salary_text | VARCHAR(255) | | YES | Original salary text | `app/models/job_posting.py` |
| original_currency | VARCHAR(10) | | YES | Original currency | `app/models/job_posting.py` |
| original_company | VARCHAR(255) | | YES | Original company name | `app/models/job_posting.py` |
| payload | JSONB | | YES | Original payload | `app/models/job_posting.py` |
| first_seen_at | DATETIME | | YES (default now()) | First seen timestamp | `app/models/job_posting.py` |
| last_seen_at | DATETIME | | YES (default now(), onupdate) | Last seen timestamp | `app/models/job_posting.py` |
| posted_at | DATETIME | | YES | Original posting date | `app/models/job_posting.py` |
| expires_at | DATETIME | | YES | Expiry date | `app/models/job_posting.py` |
| is_active | BOOLEAN | INDEX | YES (default True) | Active flag | `app/models/job_posting.py` |

**Unique Index:** (source, source_job_id)
**Composite Index:** (canonical_job_id, is_active)

## 12.3 Recommendations Domain

### Table: `recommendation_runs`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Run identifier | `app/models/recommendation_run.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | Target user | `app/models/recommendation_run.py` |
| retrieval_method | VARCHAR(50) | NOT NULL | NO | semantic/hybrid/lexical | `app/models/recommendation_run.py` |
| candidate_pool_size | INTEGER | | YES (default 0) | Initial pool size | `app/models/recommendation_run.py` |
| final_pool_size | INTEGER | | YES (default 0) | Final pool size | `app/models/recommendation_run.py` |
| embedding_model | VARCHAR(100) | | YES | Model used | `app/models/recommendation_run.py` |
| embedding_dim | INTEGER | | YES | Embedding dimensions | `app/models/recommendation_run.py` |
| reranker_model | VARCHAR(100) | | YES | Reranker model used | `app/models/recommendation_run.py` |
| scoring_config | JSONB | | YES | Scoring weights snapshot | `app/models/recommendation_run.py` |
| latency_ms | FLOAT | | YES | Pipeline latency | `app/models/recommendation_run.py` |
| agent_decisions | JSONB | | YES | Agent decision log | `app/models/recommendation_run.py` |
| started_at | DATETIME | | YES (default now()) | Start timestamp | `app/models/recommendation_run.py` |
| completed_at | DATETIME | | YES | Completion timestamp | `app/models/recommendation_run.py` |
| status | VARCHAR(20) | | YES (default "running") | running/completed/failed | `app/models/recommendation_run.py` |
| error_message | TEXT | | YES | Error details | `app/models/recommendation_run.py` |

### Table: `recommendations`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Recommendation identifier | `app/models/recommendation.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | Target user | `app/models/recommendation.py` |
| job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Recommended job | `app/models/recommendation.py` |
| match_score | FLOAT | NOT NULL | NO | Overall match score (0-1) | `app/models/recommendation.py` |
| rank | INTEGER | | YES | Ranking position | `app/models/recommendation.py` |
| score_breakdown | JSONB | | YES | Detailed score breakdown | `app/models/recommendation.py` |
| retrieval_method | VARCHAR(50) | | YES | Retrieval method used | `app/models/recommendation.py` |
| candidate_pool_position | INTEGER | | YES | Position in candidate pool | `app/models/recommendation.py` |
| explanation | TEXT | | YES | LLM-generated explanation | `app/models/recommendation.py` |
| recommendation_run_id | UUID | FK→recommendation_runs.id (SET NULL) | YES | Linked run | `app/models/recommendation.py` |
| created_at | DATETIME | | YES (default now()) | Creation timestamp | `app/models/recommendation.py` |

### Table: `saved_jobs`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Save identifier | `app/models/recommendation.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | User who saved | `app/models/recommendation.py` |
| job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Saved job | `app/models/recommendation.py` |
| saved_at | DATETIME | | YES (default now()) | Save timestamp | `app/models/recommendation.py` |

**Unique Constraint:** (user_id, job_id) — Migration 006

## 12.4 Notifications Domain

### Table: `notifications`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Notification identifier | `app/models/notification.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | Target user | `app/models/notification.py` |
| job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Related job | `app/models/notification.py` |
| type | VARCHAR(30) | NOT NULL | NO | new_job/high_match/saved_update | `app/models/notification.py` |
| match_score | FLOAT | | YES | Match score at notification time | `app/models/notification.py` |
| status | VARCHAR(20) | NOT NULL (default "pending") | NO | pending/sent/failed | Migration 006 |
| attempted_at | DATETIME | | YES | Last attempt timestamp | Migration 006 |
| sent_at | DATETIME | | YES | Send timestamp | `app/models/notification.py` |
| failure_reason | TEXT | | YES | Failure details | Migration 006 |
| retry_count | INTEGER | NOT NULL (default 0) | NO | Retry counter | Migration 006 |
| dedupe_key | VARCHAR(255) | UNIQUE, NOT NULL | NO | Deduplication key | Migration 006 |
| digest_id | UUID | INDEX | YES | Digest batch identifier | Migration 006 |
| created_at | DATETIME | NOT NULL (default now()) | NO | Creation timestamp | Migration 006 |
| opened | BOOLEAN | | YES (default False) | Open tracking | `app/models/notification.py` |

## 12.5 Interactions Domain

### Table: `user_interactions`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Interaction identifier | `app/models/user_interaction.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | User | `app/models/user_interaction.py` |
| job_id | UUID | FK→jobs.id (CASCADE), INDEX | NO | Job interacted with | `app/models/user_interaction.py` |
| interaction_type | VARCHAR(50) | NOT NULL, INDEX | NO | Type of interaction | `app/models/user_interaction.py` |
| metadata | JSONB | | YES | Additional metadata | `app/models/user_interaction.py` |
| source | VARCHAR(50) | | YES | search/recommendation/notification | `app/models/user_interaction.py` |
| recommendation_run_id | UUID | FK→recommendation_runs.id (SET NULL) | YES | Linked run | `app/models/user_interaction.py` |
| created_at | DATETIME | | YES (default now()) | Timestamp | `app/models/user_interaction.py` |

**Valid interaction types:** impression, view, save, unsave, dismiss, apply_clicked, marked_relevant, marked_irrelevant, notification_opened

## 12.6 Ingestion/Audit Domain

### Table: `ingestion_runs`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Run identifier | `app/models/ingestion_run.py` |
| source | VARCHAR(50) | NOT NULL | NO | Data source | `app/models/ingestion_run.py` |
| started_at | DATETIME | | YES (default now()) | Start timestamp | `app/models/ingestion_run.py` |
| finished_at | DATETIME | | YES | End timestamp | `app/models/ingestion_run.py` |
| records_fetched | INTEGER | | YES (default 0) | Records fetched | `app/models/ingestion_run.py` |
| records_inserted | INTEGER | | YES (default 0) | Records inserted | `app/models/ingestion_run.py` |
| records_skipped | INTEGER | | YES (default 0) | Records skipped | `app/models/ingestion_run.py` |
| errors | INTEGER | | YES (default 0) | Error count | `app/models/ingestion_run.py` |
| status | VARCHAR(30) | | YES (default "running") | running/completed/completed_with_errors/failed | Migration 007 |
| error_message | TEXT | | YES | Error details | `app/models/ingestion_run.py` |

### Table: `processing_errors`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Error identifier | `app/models/processing_error.py` |
| ingestion_run_id | UUID | FK→ingestion_runs.id (SET NULL), INDEX | YES | Linked run | `app/models/processing_error.py` |
| raw_job_id | UUID | FK→raw_jobs.id (SET NULL), INDEX | YES | Failed raw job | `app/models/processing_error.py` |
| error_type | VARCHAR(100) | NOT NULL | NO | Error category | `app/models/processing_error.py` |
| error_message | TEXT | | YES | Error details | `app/models/processing_error.py` |
| stack_trace | TEXT | | YES | Full stack trace | `app/models/processing_error.py` |
| source | VARCHAR(50) | | YES | Data source | `app/models/processing_error.py` |
| source_job_id | VARCHAR(255) | | YES | Source-specific ID | `app/models/processing_error.py` |
| retry_count | INTEGER | | YES (default 0) | Retry count | `app/models/processing_error.py` |
| resolved | BOOLEAN | | YES (default False) | Resolution status | `app/models/processing_error.py` |
| created_at | DATETIME | | YES (default now()) | Timestamp | `app/models/processing_error.py` |

**Valid error types:** salary_parse_error, location_parse_error, embedding_error, skill_extraction_error, dedup_error, validation_error, unknown_error

## 12.7 Security Domain

### Table: `token_blacklist`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Record identifier | `app/models/token_blacklist.py` |
| token_jti | VARCHAR(64) | UNIQUE, NOT NULL | NO | JWT token JTI claim | `app/models/token_blacklist.py` |
| user_id | UUID | FK→users.id (CASCADE), INDEX | NO | Token owner | `app/models/token_blacklist.py` |
| reason | VARCHAR(50) | | YES (default "logout") | Blacklist reason | `app/models/token_blacklist.py` |
| blacklisted_at | DATETIME | | YES (default now()) | Blacklist timestamp | `app/models/token_blacklist.py` |
| expires_at | DATETIME | NOT NULL | NO | Token expiry | `app/models/token_blacklist.py` |

**Valid reasons:** logout, password_reset, account_deactivated, security

## 12.8 Normalisation Domain

### Table: `normalization_aliases`
| Field | Data Type | Key/Constraint | Nullable | Purpose | Evidence |
|-------|-----------|----------------|----------|---------|----------|
| id | UUID | PK | NO | Alias identifier | `app/models/normalization_alias.py` |
| kind | VARCHAR(20) | NOT NULL, CHECK (category/location) | NO | Alias type | `app/models/normalization_alias.py` |
| alias | VARCHAR(255) | NOT NULL | NO | Raw alias value | `app/models/normalization_alias.py` |
| canonical_value | VARCHAR(255) | NOT NULL | NO | Canonical value | `app/models/normalization_alias.py` |
| is_active | BOOLEAN | NOT NULL (default True) | NO | Active flag | `app/models/normalization_alias.py` |
| created_at | DATETIME | NOT NULL (default now()) | NO | Creation timestamp | `app/models/normalization_alias.py` |
| updated_at | DATETIME | | YES (onupdate) | Update timestamp | `app/models/normalization_alias.py` |

**Unique Index:** (kind, alias)

---

# 13. DATABASE RELATIONSHIPS

| Entity A | Entity B | Relationship | Cardinality | Foreign Key | Evidence |
|----------|----------|--------------|-------------|-------------|----------|
| users | user_profiles | has one | 1:1 | user_profiles.user_id → users.id | `app/models/user.py` |
| users | notification_preferences | has one | 1:1 | notification_preferences.user_id → users.id | `app/models/user.py` |
| users | recommendations | has many | 1:N | recommendations.user_id → users.id | `app/models/recommendation.py` |
| users | saved_jobs | has many | 1:N | saved_jobs.user_id → users.id | `app/models/recommendation.py` |
| users | notifications | has many | 1:N | notifications.user_id → users.id | `app/models/notification.py` |
| users | user_interactions | has many | 1:N | user_interactions.user_id → users.id | `app/models/user_interaction.py` |
| users | token_blacklist | has many | 1:N | token_blacklist.user_id → users.id | `app/models/token_blacklist.py` |
| users | recommendation_runs | has many | 1:N | recommendation_runs.user_id → users.id | `app/models/recommendation_run.py` |
| jobs | job_skills | has many | 1:N | job_skills.job_id → jobs.id | `app/models/job.py` |
| jobs | job_postings | has many | 1:N | job_postings.canonical_job_id → jobs.id | `app/models/job_posting.py` |
| jobs | recommendations | has many | 1:N | recommendations.job_id → jobs.id | `app/models/recommendation.py` |
| jobs | saved_jobs | has many | 1:N | saved_jobs.job_id → jobs.id | `app/models/recommendation.py` |
| jobs | notifications | has many | 1:N | notifications.job_id → jobs.id | `app/models/notification.py` |
| jobs | user_interactions | has many | 1:N | user_interactions.job_id → jobs.id | `app/models/user_interaction.py` |
| raw_jobs | job_postings | has many | 1:N | job_postings.raw_job_id → raw_jobs.id | `app/models/job_posting.py` |
| raw_jobs | processing_errors | has many | 1:N | processing_errors.raw_job_id → raw_jobs.id | `app/models/processing_error.py` |
| ingestion_runs | raw_jobs | has many | 1:N | raw_jobs.ingestion_run_id → ingestion_runs.id | `app/models/job.py` |
| ingestion_runs | processing_errors | has many | 1:N | processing_errors.ingestion_run_id → ingestion_runs.id | `app/models/processing_error.py` |
| recommendation_runs | recommendations | has many | 1:N | recommendations.recommendation_run_id → recommendation_runs.id | `app/models/recommendation.py` |
| recommendation_runs | user_interactions | has many | 0:N | user_interactions.recommendation_run_id → recommendation_runs.id | `app/models/user_interaction.py` |
| jobs | raw_jobs | belongs to | N:1 | jobs.raw_job_id → raw_jobs.id | `app/models/job.py` |

---

# 14. VECTOR STORAGE

| Data | Storage | Purpose | Relationship |
|------|---------|---------|--------------|
| Job embedding | jobs.embedding (Vector(768)) | Semantic job search, cosine similarity | 1:1 with jobs table row |
| Profile embedding | user_profiles.profile_embedding (Vector(768)) | User profile semantic matching | 1:1 with user_profiles table row |
| HNSW index | ix_jobs_embedding_hnsw (vector_cosine_ops, m=16, ef_construction=64) | Fast approximate nearest neighbor search | On jobs.embedding |
| Full-text search vector | jobs.search_vector (TSVECTOR) | PostgreSQL full-text search | Computed from title_clean + description |
| GIN index | ix_jobs_search_vector | Fast full-text search | On jobs.search_vector |

**Metadata mapping:** Vectors stored inline in their respective tables (no separate vector store). Each vector maps 1:1 to its parent record via the table's primary key.

**Fallback:** When pgvector is unavailable, numpy cosine similarity is used (`app/services/vector.py` `_python_search`).

---

# 15. API AND EXTERNAL SYSTEMS

| External System | Connected Component | API/Protocol | Data Sent | Data Received | Purpose | Evidence |
|-----------------|--------------------|--------------|-----------|---------------|---------|----------|
| Adzuna API | AdzunaSource | HTTPS GET `api.adzuna.com/v1/api/jobs/{country}/search/{page}` | app_id, app_key, results_per_page, what | JSON (job listings) | Fetch job data | `app/ingestion/adzuna_source.py` |
| Reed API (search) | ReedSource | HTTPS GET `reed.co.uk/api/1.0/search` | keywords, resultsToTake, location, salary range (HTTP Basic Auth) | JSON (job IDs) | Fetch job listings | `app/ingestion/reed_source.py` |
| Reed API (detail) | ReedSource | HTTPS GET `reed.co.uk/api/1.0/jobs/{job_id}` | job_id (HTTP Basic Auth) | JSON (job detail) | Fetch job details | `app/ingestion/reed_source.py` |
| We Work Remotely | WWRScraper | HTTP GET `weworkremotely.com/remote-jobs.rss` | None | RSS XML feed | Fetch remote jobs | `app/ingestion/wwr_scraper.py` |
| Groq LLM API | RAG, QueryUnderstanding, LLMReranker | HTTPS POST `api.groq.com/openai/v1/chat/completions` | model, messages, temperature, max_tokens | LLM response text | Explanation, query analysis, reranking | `app/services/rag.py` |
| Gmail SMTP | EmailService | SMTP/TLS `smtp.gmail.com:587` | Email (MIMEMultipart), STARTTLS, login | SMTP response | Send notification/reset emails | `app/services/email.py` |
| BGE Embedding Model | EmbeddingService | Local (sentence-transformers) | Text input | 768-dim float vector | Generate embeddings | `app/services/embedding.py` |
| Cross-Encoder Reranker | RerankerService | Local (sentence-transformers) | Query + document pairs | Float scores | Rerank search results | `app/services/reranker.py` |

---

# 16. AGENT ARCHITECTURE

## 16.1 RecommendationAgent

| Node/Step | Purpose | Input | Output | Tool/Service | Next Node | Condition | Evidence |
|-----------|---------|-------|--------|-------------|-----------|-----------|----------|
| Compute Profile Embedding | Generate profile vector if missing | UserProfile | profile_embedding | Embedding Service | Retrieve Candidates | embedding is None | `app/agents/recommendation_agent.py` |
| Retrieve Candidates | Initial semantic retrieval (top 30) | profile_embedding | Candidate jobs + similarities | pgvector <=> operator | Score Candidates | Always | `app/agents/recommendation_agent.py` |
| Score Candidates | 7-signal weighted scoring | Profile + candidates + skills | Scored candidates with MatchBreakdown | Scoring Service, FeedbackLoop | Expand Pool? | Always | `app/agents/recommendation_agent.py` |
| Expand Pool | Expand to 80 if avg score < 0.35 | Scored candidates | More candidates | pgvector (wider search) | Filter | avg_score < 0.35 | `app/agents/recommendation_agent.py` |
| Filter | Apply hard constraints + min score | Scored candidates | Filtered list | None (pure logic) | Collapse Duplicates | Always | `app/agents/recommendation_agent.py` |
| Collapse Duplicates | rapidfuzz dedup | Filtered list | Deduplicated list | rapidfuzz | Rerank? | Always | `app/agents/recommendation_agent.py` |
| Rerank | Cross-encoder reranking (if pool > 20) | Deduplicated list | Reranked list | Cross-Encoder | Persist | pool > 20 | `app/agents/recommendation_agent.py` |
| Persist | Save to recommendations table | Top N scored | Recommendation records | Database | Trigger Notifications | Always | `app/agents/recommendation_agent.py` |
| Trigger Notifications | Async notification dispatch | User ID | Background task | Notification Trigger | End | Always | `app/agents/recommendation_agent.py` |

## 16.2 NotificationAgent

| Node/Step | Purpose | Input | Output | Tool/Service | Next Node | Condition | Evidence |
|-----------|---------|-------|--------|-------------|-----------|-----------|----------|
| Get New Jobs | Find jobs since last processing | Since timestamp | New job list | Database | Get Active Users | Always | `app/agents/notification_agent.py` |
| Get Active Users | Get users with notifications enabled | Frequency filter | User list | Database | Process Per User | Always | `app/agents/notification_agent.py` |
| Process Per User | Generate notification candidates | User + new_jobs | Candidate list | Scoring Service | Deliver | Always | `app/agents/notification_agent.py` |
| New Job Candidates | Score new jobs against profile | Profile + prefs + jobs | High-match candidates | Scoring Service, numpy cosine | Saved Job Candidates | Always | `app/agents/notification_agent.py` |
| Saved Job Candidates | Find updates to saved jobs | User | Related job candidates | Database | Recommendation Candidate | Always | `app/agents/notification_agent.py` |
| Recommendation Candidate | Check for top recommendation changes | User | Recommendation candidate | Database | Deliver | Always | `app/agents/notification_agent.py` |
| Deliver | Send email digest if candidates exist | Candidates + user prefs | Email sent | Email Service, Database | End | candidates exist AND email enabled | `app/agents/notification_agent.py` |

---

# 17. SECURITY BOUNDARIES

| Boundary | Mechanism | Components | Evidence |
|----------|-----------|------------|----------|
| Authentication (API) | JWT tokens (python-jose, HS256) | Auth Module (API), deps.py | `app/core/security.py`, `app/core/deps.py` |
| Authentication (Flask) | Flask-Login sessions | Auth Module (Flask) | `webapp/app.py` |
| Password Storage | bcrypt (12 rounds) | Auth Module | `app/core/security.py` |
| Token Revocation | Token blacklist (token_jti) | Token Blacklist, deps.py | `app/models/token_blacklist.py` |
| Admin Authorization | is_admin check | Admin Guard, deps.py | `app/core/deps.py`, `webapp/routes/admin_guard.py` |
| CSRF Protection | Flask-WTF CSRFProtect | Flask Web UI | `webapp/app.py` |
| Rate Limiting | SlowAPI (FastAPI), Flask-Limiter (Flask) | Both servers | `app/main.py`, `webapp/app.py` |
| CORS | FastAPI CORSMiddleware | FastAPI API | `app/main.py` |
| Secret Management | Pydantic Settings + .env | Configuration | `app/config.py` |
| Password Reset | Time-limited JWT tokens (15 min expiry) | Password Reset Service | `app/services/password_reset.py` |
| Input Validation | Pydantic models | All API schemas | All `app/api/*.py` files |
| SQL Injection Prevention | SQLAlchemy ORM parameterized queries | All database access | Throughout codebase |

---

# 18. SYSTEM ARCHITECTURE DIAGRAM SPECIFICATION

## A. Actors
1. **End User (Job Seeker)** — Uses Flask web UI to search jobs, view recommendations, manage profile
2. **Administrator** — Uses admin dashboard to manage ingestion, jobs, aliases
3. **System Scheduler** — APScheduler background processes

## B. External Systems
1. **Adzuna API** — Job data source (HTTPS REST)
2. **Reed.co.uk API** — Job data source (HTTPS REST, Basic Auth)
3. **We Work Remotely** — Job data source (RSS feed)
4. **Groq API (llama-3.3-70b-versatile)** — LLM inference (HTTPS REST, OpenAI-compatible)
5. **Gmail SMTP** — Email delivery (SMTP/TLS)
6. **PostgreSQL 16 + pgvector** — Database (runs in Docker container)

## C. Frontend/User Layer
1. **Flask Web UI** (port 5000) — `webapp/app.py`
   - Landing page, Home dashboard, Search results, Job detail, Recommendations, Profile, Saved jobs, Admin dashboard
   - Flask-Login session management
   - Jinja2 template rendering
   - CSRF protection (Flask-WTF)

## D. Backend/API Layer
1. **FastAPI REST API** (port 8000) — `app/main.py`
   - 38 endpoints across 8 route modules
   - SlowAPI rate limiting
   - CORS middleware
2. **Auth Module** — JWT tokens, bcrypt passwords, token blacklist
3. **Users Module** — Profile CRUD, notification preferences
4. **Jobs Module** — Search (4 modes), saved jobs, skill/company search
5. **Recommendations Module** — Recommendation generation, explanations
6. **Interactions Module** — User interaction tracking
7. **Notifications Module** — Notification history and stats
8. **Admin Module** — Ingestion runs, job CRUD, aliases, reprocessing

## E. AI/ML/Agent Layer
1. **Embedding Service** — BAAI/bge-base-en-v1.5 (768-dim, local)
2. **Reranker Service** — cross-encoder/ms-marco-MiniLM-L-6-v2 (local)
3. **LLM Client** — Groq API (llama-3.3-70b-versatile)
4. **RAG Explanation Generator** — Chain-of-thought explanation with validation
5. **Query Understanding** — LLM intent classification + term expansion
6. **LLM Reranker** — Profile-aware re-scoring
7. **Recommendation Agent** — Multi-step pipeline with decision logging
8. **Notification Agent** — Frequency-aware notification delivery
9. **Scoring Service** — 7-signal weighted match scoring (v3.0)
10. **Feedback Loop** — Interaction-based personalization

## F. Processing Layer
1. **Processing Pipeline** — 7-module transformation pipeline
   - Title Cleaner, Salary Parser, Location Normaliser, Category Normaliser
   - Skill Extractor, Dedup Service, Quality Scorer
2. **Ingestion Service** — 4 data source connectors
   - AdzunaSource, ReedSource, WWRScraper, CsvSource

## G. Data Layer
1. **PostgreSQL 16 + pgvector** — 13 tables
2. **pgvector HNSW Index** — Vector similarity search
3. **PostgreSQL TSVECTOR + GIN** — Full-text search
4. **Docker Compose** — Container orchestration

## H. Notification Layer
1. **Email Service** — SMTP email (digest, password reset)
2. **Notification Scheduler** — APScheduler (instant/daily/weekly)
3. **Ingestion Scheduler** — APScheduler (WWR 6h, daily processing)
4. **Notification Trigger** — ThreadPoolExecutor (4 threads, fire-and-forget)

## I. Connections
```
User Browser → HTTP → Flask Web UI (port 5000)
Flask Web UI → HTTP → FastAPI API (port 8000) [CORS]
Flask Web UI → SQLAlchemy → PostgreSQL
FastAPI API → SQLAlchemy → PostgreSQL
FastAPI API → Function Calls → All Backend Services
Ingestion Service → HTTPS → Adzuna API
Ingestion Service → HTTPS → Reed API
Ingestion Service → HTTP → WWR RSS
LLM Client → HTTPS → Groq API
Email Service → SMTP/TLS → Gmail SMTP
Embedding Service → Local Model → BGE (768-dim)
Reranker → Local Model → Cross-Encoder
Scheduler → Function Calls → Agent Services
Agent Services → Function Calls → Database, Services
```

## J. Architecture Boundaries
- **Client ↔ Server:** HTTP (Flask port 5000, FastAPI port 8000)
- **Flask ↔ FastAPI:** HTTP + shared database
- **Server ↔ Database:** SQLAlchemy ORM + raw SQL (pgvector ops)
- **Server ↔ External APIs:** HTTPS, HTTP, SMTP
- **Server ↔ Local ML:** In-process function calls
- **Background ↔ Foreground:** APScheduler + ThreadPoolExecutor (same process)
- **Auth Boundary:** JWT/Session required for protected routes
- **Admin Boundary:** is_admin check for admin routes

## K. Diagram Layout Recommendation
**Layout:** 5-tier vertical layout (top to bottom):
1. **User Layer** — Browser, Actors
2. **Presentation Layer** — Flask Web UI (port 5000)
3. **API/Application Layer** — FastAPI (port 8000), all route modules, agents
4. **AI/ML + Processing Layer** — Embedding, LLM, Reranker, Processing Pipeline, Ingestion
5. **Data Layer** — PostgreSQL + pgvector (Docker)

**Side panels:**
- Left: External Systems (Adzuna, Reed, WWR, Groq, Gmail SMTP)
- Right: Background Services (Schedulers, ThreadPoolExecutor)

---

# 19. SYSTEM FLOW DIAGRAM SPECIFICATION

## A. Start Point
System startup → `app/main.py` on_startup() → init_db() → Start schedulers (if enabled)

## B. Inputs
1. External data sources (Adzuna, Reed, WWR RSS, CSV files)
2. User interactions (search, recommendations, profile updates)
3. Scheduler triggers (ingestion every 6h, notifications every 5min/daily/weekly)

## C. Processing Steps — Data Ingestion Pipeline
```
START (Scheduler Trigger / Manual Script)
↓
STEP 1: Ingestion Scheduler fires (every 6h for WWR, daily for processing)
↓
STEP 2: Data Source Connector fetches raw jobs
├── AdzunaSource → HTTPS GET → JSON
├── ReedSource → HTTPS GET (Basic Auth) → JSON (search + detail)
├── WWRScraper → HTTP GET → RSS feed
└── CsvSource → File Read → CSV rows
↓
STEP 3: Raw jobs stored in raw_jobs table (JSONB payload)
↓
STEP 4: Processing Pipeline processes each raw job
│   ↓
│   STEP 4a: Title Cleaner → clean_title (regex noise removal)
│   ↓
│   STEP 4b: Salary Parser → ParsedSalary (regex extraction, period detection)
│   ↓
│   STEP 4c: Location Normaliser → Structured location (city, country, UK fields, remote)
│   ↓
│   STEP 4d: Category Normaliser → Canonical category (keyword rules, fuzzy match)
│   ↓
│   STEP 4e: Skill Extractor → Skill list (dictionary matching, context classification)
│   ↓
│   STEP 4f: Dedup Hash Generator → SHA-256 hash
│   ↓
│   DECISION: dedup_hash exists in DB?
│   ├── YES → Skip (increment processing_attempts)
│   └── NO → Continue
│   ↓
│   STEP 4g: Embedding Generator → 768-dim vector (BGE model)
│   ↓
│   STEP 4h: Quality Scorer → QualityScore (5 dimensions, 0-100)
│   ↓
│   STEP 4i: Store Job → INSERT INTO jobs + job_skills + job_postings
│   ↓
│   DECISION: Any error?
│   ├── YES → Log ProcessingError, rollback
│   └── NO → Mark raw_job.processed = True
↓
STEP 5: Ingestion run summary updated
↓
END
```

## D. Processing Steps — Recommendation Pipeline
```
START (User requests recommendations via GET /api/me/recommendations)
↓
STEP 1: Auth check (JWT valid, not blacklisted, user active)
↓
STEP 2: Fetch UserProfile from database
↓
DECISION: Profile has skills or headline?
├── NO → HTTP 400 error
└── YES → Continue
↓
STEP 3: Check/generate profile embedding
├── embedding exists → Use existing
└── embedding NULL → build_profile_text() → generate_embedding() → Save
↓
STEP 4: Retrieve candidates via pgvector cosine distance (top 30)
↓
STEP 5: Score candidates (7-signal weighted scoring)
├── Semantic similarity (25%)
├── Skill overlap (30%, bidirectional, alias-resolved)
├── Location fit (15%, tiered)
├── Salary fit (12%, currency-converted)
├── Experience fit (8%)
├── Job type fit (5%)
└── Recency score (5%)
↓
STEP 6: Apply feedback loop adjustments (boost/suppress from interactions)
↓
DECISION: Average score < 0.35?
├── YES → Expand pool to 80 candidates, re-score
└── NO → Continue with 30
↓
STEP 7: Filter by hard constraints (location, remote, salary, job type)
↓
STEP 8: Filter by minimum score threshold
↓
STEP 9: Collapse duplicates (rapidfuzz)
↓
DECISION: Pool size > 20?
├── YES → Cross-encoder rerank (blend 0.7×original + 0.3×rerank)
└── NO → Skip reranking
↓
STEP 10: Sort by score, trim to top_n
↓
STEP 11: Persist to recommendations table
├── DELETE old recommendations for user
└── INSERT new recommendations
↓
STEP 12: Async trigger notification check (ThreadPoolExecutor)
↓
STEP 13: Return recommendations with breakdown
↓
END
```

## E. Processing Steps — Search Pipeline
```
START (User submits search via GET /api/jobs/search/*)
↓
STEP 1: Normalise query text (lowercase, strip)
↓
STEP 2: Query Understanding (LLM intent classification + expansion)
├── Groq API call → expanded_terms
└── Fallback: use original query only
↓
STEP 3: Determine query type (is_technical?)
├── Short/technical (≤3 tokens, in skill dict) → Evidence search path
└── Long/natural language → Semantic search path
↓
DECISION: Technical query?
├── YES → STEP 4a: Evidence Search
│   ↓
│   STEP 4a-i: Build lexical evidence query (ILIKE patterns on title, description, requirements, skills)
│   ↓
│   STEP 4a-ii: Execute SQL with lexical conditions
│   ↓
│   STEP 4a-iii: Extract match evidence per job
│   ↓
│   STEP 4a-iv: Compute lexical relevance score
│   ↓
│   DECISION: Enough results (≥5)?
│   ├── YES → Continue with lexical results
│   └── NO → Semantic fallback (pgvector cosine similarity)
│
└── NO → STEP 4b: Semantic Search
    ↓
    STEP 4b-i: Generate query embedding (BGE model)
    ↓
    STEP 4b-ii: pgvector cosine similarity search
    ↓
    STEP 4b-iii: Build result dictionaries
↓
STEP 5: Collapse duplicates (rapidfuzz)
↓
STEP 6: Filter by quality score (≥40)
↓
DECISION: rerank=True?
├── YES → Cross-encoder reranking (blend 0.7+0.3)
└── NO → Skip
↓
DECISION: llm_rerank=True AND user authenticated AND has profile?
├── YES → LLM re-scoring (Groq API, blend 0.4)
└── NO → Skip
↓
STEP 7: Return results
↓
END
```

## F. Processing Steps — Notification Pipeline
```
START (Scheduler trigger every 5min / daily / weekly OR recommendation trigger)
↓
STEP 1: Determine frequency (instant/daily/weekly)
↓
STEP 2: Get new jobs since last processing
↓
STEP 3: Get active users with matching frequency
↓
STEP 4: For each user:
│   ↓
│   STEP 4a: Load profile + preferences
│   ↓
│   STEP 4b: Generate candidates from 3 sources:
│   │   ├── New high-match jobs (cosine similarity + scoring)
│   │   ├── Saved job similar updates
│   │   └── Top recommendation changes
│   ↓
│   STEP 4c: Filter by min_match_score threshold
│   ↓
│   STEP 4d: Deduplicate (dedupe_key)
│   ↓
│   STEP 4e: Limit to digest size (5 jobs)
│   ↓
│   DECISION: Candidates exist AND email enabled?
│   ├── YES → STEP 5: Send email digest
│   │   ↓
│   │   STEP 5a: Build HTML email (job table with titles, companies, scores)
│   │   ↓
│   │   STEP 5b: SMTP send (STARTTLS, Gmail)
│   │   ↓
│   │   STEP 5c: Record notifications in DB
│   │   ↓
│   │   DECISION: Send successful?
│   │   ├── YES → Mark status="sent"
│   │   └── NO → Mark status="failed", increment retry_count
│   │
│   └── NO → Skip (log, no email)
↓
STEP 6: Update last_processed_at
↓
END
```

## G. Processing Steps — User Registration & Authentication
```
START (User submits registration/login)
↓
REGISTRATION:
├── Validate password complexity
├── Check email uniqueness
├── Hash password (bcrypt, 12 rounds)
├── INSERT user + default profile + default notification prefs
├── Return 201 Created
↓
LOGIN:
├── Find user by email
├── Verify password (bcrypt)
├── Check is_active
├── Create JWT (sub=user_id, jti=uuid, exp=24h)
├── Return JWT token
↓
REQUEST PROCESSING:
├── Extract JWT from Authorization header
├── Decode and validate (purpose="access")
├── Check token_jti NOT in blacklist
├── Load user from DB
├── Return user (or 401)
↓
LOGOUT:
├── Decode JWT to get jti
├── INSERT into token_blacklist
├── Return 200
↓
END
```

## H. Decision Points (Summary)
1. D01: JWT valid + not blacklisted + user active? → Allow/401
2. D02: User is admin? → Allow/403
3. D03: Password valid? → Proceed/422
4. D04: Email exists? → 409/Create
5. D05: Credentials correct? → JWT/401
6. D08: Skills/headline present? → Recommend/400
7. D09: Query is technical? → Evidence search/Semantic search
8. D10: Enough lexical results (≥5)? → Use results/Semantic fallback
9. D11: dedup_hash exists? → Skip/Insert
10. D13: Avg score < 0.35? → Expand pool/Keep 30
11. D14: Pool > 20? → Cross-encoder rerank/Skip
12. D15: SMTP configured? → Send/Skip
13. D17: Score ≥ min_match_score? → Notify/Skip
14. D20: Match tier (≥0.75/≥0.45/else)? → Select prompt tier

## I. Error Paths
- Ingestion API failure → retry_with_backoff (3 retries) → log ProcessingError
- Embedding failure → log ProcessingError, mark unprocessed
- LLM API failure → retry (max 2) → fallback template explanation
- SMTP failure → log, mark notification failed
- JWT blacklist hit → 401 Unauthorized
- Rate limit exceeded → 429 Too Many Requests
- pgvector unavailable → numpy fallback

## J. End Points
- Ingestion pipeline: raw_jobs → jobs table populated
- Recommendation pipeline: recommendations table populated
- Notification pipeline: emails sent, notifications table populated
- Search pipeline: ranked results returned to user

---

# 20. DATABASE/SCHEMA DIAGRAM SPECIFICATION

## A. Database Technology
PostgreSQL 16 with pgvector extension, Docker container, SQLAlchemy ORM, Alembic migrations

## B. Entities/Tables (13 total)

### 1. users (Authentication & Account)
- PK: id (UUID)
- UNIQUE: email
- INDEX: email
- Fields: id, email, password_hash, is_active, is_admin, created_at

### 2. user_profiles (User Preferences & Embeddings)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- UNIQUE: user_id
- Fields: id, user_id, full_name, headline, skills (ARRAY), experience_years, experience_level, preferred_locations (ARRAY), preferred_job_types (ARRAY), min_salary, salary_currency, career_interests, profile_embedding (Vector(768))

### 3. notification_preferences (Notification Settings)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- UNIQUE: user_id
- CHECK: frequency IN ('instant', 'daily', 'weekly')
- CHECK: min_match_score BETWEEN 0 AND 1
- Fields: id, user_id, email_enabled, min_match_score, frequency, timezone, last_processed_at, last_digest_sent_at

### 4. raw_jobs (Raw Ingested Data)
- PK: id (UUID)
- FK: ingestion_run_id → ingestion_runs.id (SET NULL)
- UNIQUE INDEX: (source, source_job_id)
- INDEX: processed, ingestion_run_id
- Fields: id, source, source_job_id, payload (JSONB), fetched_at, processed, ingestion_run_id, processing_attempts

### 5. jobs (Normalised Job Vacancies)
- PK: id (UUID)
- FK: raw_job_id → raw_jobs.id
- UNIQUE INDEX: dedup_hash
- INDEX: category, is_active, source, created_at
- HNSW INDEX: embedding (vector_cosine_ops, m=16, ef_construction=64)
- GIN INDEX: search_vector (TSVECTOR)
- COMPUTED: search_vector = to_tsvector('english', coalesce(title_clean, '') || ' ' || coalesce(description, ''))
- CHECK: salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max
- Fields: id, raw_job_id, title, title_clean, company, description, description_clean, requirements, responsibilities, location_city, location_country, remote, uk_country, uk_region, county, postcode_area, latitude, longitude, workplace_type, salary_min, salary_max, salary_currency, salary_period, original_salary_text, annualised_gbp_salary, salary_confidence, category, job_type, contract_duration, experience_level, posted_at, closing_date, url, source, dedup_hash, is_active, quality_score, search_vector, embedding (Vector(768)), embedding_model, embedding_dim, embedded_at, source_text_hash, processing_version, created_at, updated_at

### 6. job_skills (Extracted Skills per Job)
- PK: id (UUID)
- FK: job_id → jobs.id (CASCADE)
- UNIQUE INDEX: (job_id, skill)
- INDEX: job_id
- Fields: id, job_id, skill, confidence, is_essential, extraction_method

### 7. job_postings (Source-Level Postings)
- PK: id (UUID)
- FK: canonical_job_id → jobs.id (CASCADE)
- FK: raw_job_id → raw_jobs.id (SET NULL)
- UNIQUE INDEX: (source, source_job_id)
- INDEX: (canonical_job_id, is_active)
- Fields: id, canonical_job_id, raw_job_id, source, source_job_id, source_url, original_title, original_description, original_location, original_salary_text, original_currency, original_company, payload (JSONB), first_seen_at, last_seen_at, posted_at, expires_at, is_active

### 8. recommendations (User Recommendations)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- FK: job_id → jobs.id (CASCADE)
- FK: recommendation_run_id → recommendation_runs.id (SET NULL)
- INDEX: user_id, job_id
- Fields: id, user_id, job_id, match_score, rank, score_breakdown (JSONB), retrieval_method, candidate_pool_position, explanation, recommendation_run_id, created_at

### 9. recommendation_runs (Recommendation Audit Trail)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- INDEX: user_id
- Fields: id, user_id, retrieval_method, candidate_pool_size, final_pool_size, embedding_model, embedding_dim, reranker_model, scoring_config (JSONB), latency_ms, agent_decisions (JSONB), started_at, completed_at, status, error_message

### 10. saved_jobs (User Saved Jobs)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- FK: job_id → jobs.id (CASCADE)
- UNIQUE CONSTRAINT: (user_id, job_id)
- INDEX: user_id, job_id
- Fields: id, user_id, job_id, saved_at

### 11. notifications (Notification Records)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- FK: job_id → jobs.id (CASCADE)
- UNIQUE: dedupe_key
- INDEX: user_id, job_id, digest_id
- CHECK: status IN ('pending', 'sent', 'failed')
- Fields: id, user_id, job_id, type, match_score, status, attempted_at, sent_at, failure_reason, retry_count, dedupe_key, digest_id, created_at, opened

### 12. user_interactions (User Interaction Tracking)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- FK: job_id → jobs.id (CASCADE)
- FK: recommendation_run_id → recommendation_runs.id (SET NULL)
- INDEX: user_id, job_id, interaction_type
- Fields: id, user_id, job_id, interaction_type, metadata (JSONB), source, recommendation_run_id, created_at

### 13. token_blacklist (JWT Revocation)
- PK: id (UUID)
- FK: user_id → users.id (CASCADE)
- UNIQUE: token_jti
- INDEX: user_id
- Fields: id, token_jti, user_id, reason, blacklisted_at, expires_at

### 14. ingestion_runs (Ingestion Audit Trail)
- PK: id (UUID)
- Fields: id, source, started_at, finished_at, records_fetched, records_inserted, records_skipped, errors, status, error_message

### 15. processing_errors (Processing Error Log)
- PK: id (UUID)
- FK: ingestion_run_id → ingestion_runs.id (SET NULL)
- FK: raw_job_id → raw_jobs.id (SET NULL)
- INDEX: ingestion_run_id, raw_job_id
- Fields: id, ingestion_run_id, raw_job_id, error_type, error_message, stack_trace, source, source_job_id, retry_count, resolved, created_at

### 16. normalization_aliases (Category/Location Aliases)
- PK: id (UUID)
- CHECK: kind IN ('category', 'location')
- UNIQUE INDEX: (kind, alias)
- Fields: id, kind, alias, canonical_value, is_active, created_at, updated_at

## C. Relationships
```
users ──1:1──→ user_profiles
users ──1:1──→ notification_preferences
users ──1:N──→ recommendations
users ──1:N──→ saved_jobs
users ──1:N──→ notifications
users ──1:N──→ user_interactions
users ──1:N──→ token_blacklist
users ──1:N──→ recommendation_runs

jobs ──1:N──→ job_skills
jobs ──1:N──→ job_postings
jobs ──1:N──→ recommendations
jobs ──1:N──→ saved_jobs
jobs ──1:N──→ notifications
jobs ──1:N──→ user_interactions

raw_jobs ──1:N──→ job_postings
raw_jobs ──1:N──→ processing_errors
jobs ──N:1──→ raw_jobs (raw_job_id)

ingestion_runs ──1:N──→ raw_jobs
ingestion_runs ──1:N──→ processing_errors

recommendation_runs ──1:N──→ recommendations
recommendation_runs ──1:N──→ user_interactions
```

## D. Cardinality Summary
- users → user_profiles: 1:1
- users → notification_preferences: 1:1
- users → recommendations: 1:N
- users → saved_jobs: 1:N
- users → notifications: 1:N
- users → user_interactions: 1:N
- users → token_blacklist: 1:N
- users → recommendation_runs: 1:N
- jobs → job_skills: 1:N
- jobs → job_postings: 1:N
- jobs → recommendations: 1:N
- jobs → saved_jobs: 1:N
- jobs → notifications: 1:N
- jobs → user_interactions: 1:N
- raw_jobs → job_postings: 1:N
- raw_jobs → processing_errors: 1:N
- jobs → raw_jobs: N:1
- ingestion_runs → raw_jobs: 1:N
- ingestion_runs → processing_errors: 1:N
- recommendation_runs → recommendations: 1:N
- recommendation_runs → user_interactions: 0:N

## E. Vector Storage
- **jobs.embedding:** Vector(768), HNSW index (m=16, ef_construction=64, vector_cosine_ops)
- **user_profiles.profile_embedding:** Vector(768), no dedicated index (used for profile-to-job comparison)
- **jobs.search_vector:** TSVECTOR (computed from title_clean + description), GIN index
- **Mapping:** Vectors stored inline in their parent tables. No separate vector database. Cosine distance via pgvector `<=>` operator.

## F. Schema Notes
1. **Three-tier job model:** raw_jobs (raw data) → jobs (normalised, deduplicated) → job_postings (source-level tracking). One canonical job may have multiple postings from different sources.
2. **pgvector integration:** Both jobs and user_profiles have Vector(768) columns for semantic similarity search. HNSW index on jobs.embedding for fast approximate nearest neighbor queries.
3. **Full-text search:** PostgreSQL TSVECTOR computed column with GIN index for keyword search.
4. **Audit trail:** recommendation_runs and ingestion_runs track every pipeline execution with agent decisions, latency, and error details.
5. **Deduplication:** SHA-256 dedup_hash on jobs (title+company+location+salary) with unique constraint. Fuzzy dedup via rapidfuzz at processing time.
6. **Soft deletes:** jobs.is_active flag for archival without data loss.
7. **Cascade deletes:** User deletion cascades to all related records (profiles, recommendations, notifications, interactions, etc.).

---

# 21. CROSS-DIAGRAM CONSISTENCY CHECK

## Architecture ↔ Flow
- All 48 components identified in architecture appear in at least one flow. **CONSISTENT.**
- Agent layer (C22, C25) properly represented in recommendation and notification flows. **CONSISTENT.**
- Processing layer (C29, C33-C39) properly represented in ingestion flow. **CONSISTENT.**

## Architecture ↔ Schema
- All components that read/write persistent data correspond to relevant database entities. **CONSISTENT.**
- Embedding Service → jobs.embedding, user_profiles.profile_embedding. **CONSISTENT.**
- Search Service → jobs.search_vector, jobs.embedding. **CONSISTENT.**
- Notification Agent → notifications table. **CONSISTENT.**

## Flow ↔ Schema
- Every database operation in flows corresponds to actual entities. **CONSISTENT.**
- Ingestion flow writes to: raw_jobs, jobs, job_skills, job_postings, processing_errors. All exist. **CONSISTENT.**
- Recommendation flow writes to: recommendations, recommendation_runs. All exist. **CONSISTENT.**
- Notification flow writes to: notifications. Exists. **CONSISTENT.**

## Flow ↔ APIs
- External API interactions (Adzuna, Reed, WWR, Groq, SMTP) appear consistently in both architecture and flow. **CONSISTENT.**

## Agent ↔ Architecture
- RecommendationAgent nodes (9 steps) all exist in architecture as C22. **CONSISTENT.**
- NotificationAgent nodes (7 steps) all exist in architecture as C25. **CONSISTENT.**

## Technology Consistency
- Embedding model (BAAI/bge-base-en-v1.5) used consistently across architecture, flow, and services. **CONSISTENT.**
- LLM (llama-3.3-70b-versatile via Groq) used consistently across RAG, QueryUnderstanding, LLMReranker. **CONSISTENT.**
- Cross-encoder (ms-marco-MiniLM-L-6-v2) used consistently in Reranker service. **CONSISTENT.**

**No inconsistencies found.**

---

# 22. MISSING INFORMATION

## Missing Information — System Architecture
None critical. All components, connections, and technologies are evidenced.

## Missing Information — System Flow
None critical. All flows traced from actual code.

## Missing Information — Schema
None critical. All 16 tables with all fields, types, constraints documented from migrations and models.

---

# 23. FINAL MASTER DIAGRAM SPECIFICATION

# DIAGRAM 1 — SYSTEM ARCHITECTURE

**Actors:**
- End User (Job Seeker) — Browser
- Administrator — Browser
- System Scheduler — APScheduler

**Components:**
```
LAYER 1 — USER/CLIENT:
  [Browser] ←→ HTTP

LAYER 2 — PRESENTATION:
  [Flask Web UI :5000]
    ├── Auth Routes (login, register, forgot/reset password)
    ├── Main Routes (landing, home dashboard)
    ├── Jobs Routes (search, recommendations, detail, save, explain, feed)
    ├── Profile Routes (view/edit, resume upload)
    └── Admin Routes (ingestion runs, jobs, aliases, reprocess)

LAYER 3 — API/APPLICATION:
  [FastAPI REST API :8000]
    ├── Auth API (register, login, logout, forgot, reset)
    ├── Users API (profile CRUD, notification prefs)
    ├── Jobs API (semantic, keyword, evidence, hybrid search; similar; saved; skills; company; recent)
    ├── Recommendations API (get, detail, explain)
    ├── Interactions API (log, list, summary)
    ├── Notifications API (list, stats)
    └── Admin API (ingestion runs, jobs CRUD, aliases, reprocess)
  [Auth Module] — JWT, bcrypt, token blacklist
  [Agents]
    ├── RecommendationAgent — multi-step pipeline
    └── NotificationAgent — frequency-aware delivery
  [Services]
    ├── Search Service — 4 modes + reranking
    ├── Scoring Service — 7-signal weighted (v3.0)
    ├── Feedback Loop — interaction-based personalization
    ├── Interaction Tracker — event logging
    ├── Profile Completeness — completeness calculator
    └── Preferences — validation

LAYER 4 — AI/ML:
  [Embedding Service] — BAAI/bge-base-en-v1.5 (768-dim, local)
  [Reranker Service] — cross-encoder/ms-marco-MiniLM-L-6-v2 (local)
  [LLM Client] — Groq API (llama-3.3-70b-versatile)
  [RAG Generator] — explanation with chain-of-thought
  [Query Understanding] — LLM intent + expansion
  [LLM Reranker] — profile-aware re-scoring
  [Explanation Validator] — hallucination detection

LAYER 5 — PROCESSING:
  [Processing Pipeline] — 7 modules
    ├── Title Cleaner (regex)
    ├── Salary Parser (regex)
    ├── Location Normaliser (regex + lookup)
    ├── Category Normaliser (rules + fuzzy)
    ├── Skill Extractor (dictionary)
    ├── Dedup Service (SHA-256 + rapidfuzz)
    └── Quality Scorer (5 dimensions)
  [Ingestion Service] — 4 connectors
    ├── AdzunaSource (HTTPS → Adzuna API)
    ├── ReedSource (HTTPS → Reed API)
    ├── WWRScraper (HTTP → RSS)
    └── CsvSource (File → CSV)

LAYER 6 — DATA:
  [PostgreSQL 16 + pgvector] — Docker container
    ├── 16 tables
    ├── HNSW index (embedding)
    ├── GIN index (search_vector)
    └── TSVECTOR (computed full-text)

LAYER 7 — NOTIFICATION:
  [Email Service] — SMTP/TLS → Gmail
  [Notification Scheduler] — APScheduler (5min/daily/weekly)
  [Ingestion Scheduler] — APScheduler (6h WWR, daily processing)
  [Notification Trigger] — ThreadPoolExecutor (4 threads)

EXTERNAL SYSTEMS:
  ├── Adzuna API (HTTPS REST)
  ├── Reed.co.uk API (HTTPS REST, Basic Auth)
  ├── We Work Remotely (RSS feed)
  ├── Groq API (HTTPS REST, OpenAI-compatible)
  └── Gmail SMTP (SMTP/TLS, port 587)
```

**Connections:**
```
Browser → HTTP → Flask Web UI :5000
Flask Web UI → HTTP → FastAPI API :8000 [CORS]
Flask Web UI → SQLAlchemy → PostgreSQL
FastAPI API → SQLAlchemy → PostgreSQL
FastAPI API → Function → All Services
Ingestion → HTTPS → Adzuna/Reed
Ingestion → HTTP → WWR RSS
Ingestion → File → CSV
LLM Client → HTTPS → Groq API
Email → SMTP/TLS → Gmail
Scheduler → Function → Agents
Agents → Function → DB, Services
ThreadPoolExecutor → Function → NotificationAgent
```

**External Systems:**
- Adzuna API — `api.adzuna.com/v1/api/jobs/{country}/search/{page}` (query param auth)
- Reed API — `reed.co.uk/api/1.0/search` + `/jobs/{id}` (HTTP Basic Auth)
- We Work Remotely — `weworkremotely.com/remote-jobs.rss` (no auth)
- Groq API — `api.groq.com/openai/v1/chat/completions` (Bearer token)
- Gmail SMTP — `smtp.gmail.com:587` (STARTTLS + login)

**Databases:**
- PostgreSQL 16 + pgvector (Docker: `pgvector/pgvector:pg16`)
- 16 tables, HNSW vector index, GIN full-text index

**Technologies:** Python 3.11+, FastAPI, Flask, SQLAlchemy, PostgreSQL, pgvector, sentence-transformers, Groq (llama-3.3-70b-versatile), cross-encoder, APScheduler, bcrypt, JWT, Docker

**Boundaries:** Client↔Server (HTTP), Flask↔FastAPI (HTTP+shared DB), Server↔DB (SQLAlchemy), Server↔External (HTTPS/SMTP), Server↔LocalML (function calls), Background↔Foreground (same process), Auth (JWT/Session), Admin (is_admin)

---

# DIAGRAM 2 — SYSTEM PROCESS FLOW

**Start:** System startup → init_db() → start schedulers

**Main Flows:**

### Flow A: Data Ingestion
```
START
↓
[Ingestion Scheduler] fires (6h WWR / daily processing)
↓
[Data Source Connector] fetches
├── AdzunaSource → HTTPS GET → JSON
├── ReedSource → HTTPS GET (Basic Auth) → JSON
├── WWRScraper → HTTP GET → RSS
└── CsvSource → File Read → CSV
↓
[Store Raw Jobs] → raw_jobs table
↓
[Processing Pipeline] per raw job:
  clean_title → parse_salary → normalise_location → normalise_category
  → extract_skills → generate_dedup_hash
  ↓
  DECISION: dedup_hash exists?
  ├── YES → Skip
  └── NO → Continue
  ↓
  generate_embedding → score_job
  ↓
  [Store Job] → jobs + job_skills + job_postings
  ↓
  DECISION: Error?
  ├── YES → Log processing_error
  └── NO → Mark processed
↓
END
```

### Flow B: User Registration & Profile
```
START
↓
[Register] → Validate password → Hash (bcrypt) → INSERT user + profile + prefs
↓
[Login] → Verify password → Check blacklist → Create JWT → Return token
↓
[Update Profile] → Validate → Normalise skills → Generate embedding → Save
↓
END
```

### Flow C: Search
```
START
↓
[Query Understanding] → LLM intent classification → expanded_terms
↓
DECISION: Technical query?
├── YES → [Evidence Search]
│   ↓
│   Lexical evidence retrieval (ILIKE on title, description, requirements, skills)
│   ↓
│   DECISION: Enough results (≥5)?
│   ├── YES → Use lexical results
│   └── NO → Semantic fallback (pgvector cosine)
│
└── NO → [Semantic Search]
    ↓
    Query embedding → pgvector cosine similarity
↓
[Collapse Duplicates] → rapidfuzz
↓
[Filter by Quality] → score ≥ 40
↓
DECISION: rerank=True?
├── YES → [Cross-Encoder Rerank] (blend 0.7+0.3)
└── NO → Skip
↓
DECISION: llm_rerank=True + authenticated + has profile?
├── YES → [LLM Rerank] (Groq API, blend 0.4)
└── NO → Skip
↓
[Return Results]
↓
END
```

### Flow D: Recommendation Generation
```
START
↓
[Auth Check] → JWT valid + not blacklisted + active
↓
[Fetch Profile] → UserProfile from DB
↓
DECISION: Has skills or headline?
├── NO → HTTP 400
└── YES → Continue
↓
[Compute Profile Embedding] → BGE model (if missing)
↓
[Retrieve Candidates] → pgvector cosine distance (top 30)
↓
[Score Candidates] → 7-signal weighted scoring
├── Semantic (25%) + Skills (30%) + Location (15%)
├── Salary (12%) + Experience (8%) + Type (5%) + Recency (5%)
↓
[Apply Feedback Adjustments]
↓
DECISION: Avg score < 0.35?
├── YES → Expand to 80 candidates
└── NO → Keep 30
↓
[Filter] → Hard constraints + min score
↓
[Collapse Duplicates] → rapidfuzz
↓
DECISION: Pool > 20?
├── YES → [Cross-Encoder Rerank] (0.7+0.3)
└── NO → Skip
↓
[Persist] → DELETE old + INSERT new recommendations
↓
[Trigger Notifications] → ThreadPoolExecutor
↓
[Return Recommendations]
↓
END
```

### Flow E: Notification Delivery
```
START
↓
[Scheduler/Trigger] → frequency (instant/daily/weekly)
↓
[Get New Jobs] → since last processing
↓
[Get Active Users] → matching frequency, enabled
↓
Per User:
  ↓
  [Generate Candidates]
  ├── New high-match jobs (cosine + scoring)
  ├── Saved job similar updates
  └── Top recommendation changes
  ↓
  [Filter] → min_match_score threshold
  ↓
  [Deduplicate] → dedupe_key
  ↓
  [Limit] → digest size (5)
  ↓
  DECISION: Candidates + email enabled?
  ├── YES → [Build HTML Email] → [SMTP Send]
  │   ↓
  │   DECISION: Send OK?
  │   ├── YES → status="sent"
  │   └── NO → status="failed", retry_count++
  │
  └── NO → Skip
↓
[Update last_processed_at]
↓
END
```

### Flow F: Explanation Generation
```
START
↓
[Build Evidence Block] → profile + job + breakdown text
↓
[Select Prompt] → tier-based (high ≥75%, medium ≥45%, low)
↓
[LLM Call] → Groq API (llama-3.3-70b-versatile, temp=0.3)
↓
[Parse Response] → ExplanationResult
↓
[Validate] → Skill/salary/location/experience checks
↓
DECISION: Valid?
├── YES → Use explanation
└── NO → Retry (max 2) → Fallback template
↓
[Return Explanation]
↓
END
```

**Decisions:**
1. JWT valid? (Auth boundary)
2. dedup_exists? (Ingestion)
3. Technical query? (Search routing)
4. Enough lexical results? (Search fallback)
5. Rerank? (Search enhancement)
6. LLM rerank? (Search enhancement)
7. Avg score < 0.35? (Recommendation expansion)
8. Pool > 20? (Reranking threshold)
9. Candidates exist + email enabled? (Notification trigger)
10. SMTP configured? (Email availability)
11. Match tier? (Explanation prompt selection)

**Errors:**
- API failure → retry_with_backoff → log
- Embedding failure → log, skip
- LLM failure → retry → fallback
- SMTP failure → log, mark failed
- JWT blacklist → 401
- Rate limit → 429

---

# DIAGRAM 3 — DATABASE / SCHEMA

**Database:** PostgreSQL 16 + pgvector (Docker: pgvector/pgvector:pg16)

**16 Entities:**

```
┌──────────────────────────────────────────────────────────────┐
│                         USERS DOMAIN                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐     1:1     ┌──────────────────┐              │
│  │  users   │────────────→│  user_profiles   │              │
│  │──────────│             │──────────────────│              │
│  │ id (PK)  │             │ id (PK)          │              │
│  │ email    │←─UNIQUE     │ user_id (FK→users)│←─UNIQUE     │
│  │ pwd_hash │             │ full_name        │              │
│  │ is_active│             │ headline         │              │
│  │ is_admin │             │ skills[]         │              │
│  │ created_at│            │ exp_years        │              │
│  └────┬─────┘             │ exp_level        │              │
│       │                   │ pref_locations[] │              │
│       │ 1:1               │ pref_job_types[] │              │
│       ├──────────────────→│ min_salary       │              │
│       │                   │ salary_currency  │              │
│       │                   │ career_interests │              │
│       │                   │ profile_embedding│← Vector(768) │
│       │                   └──────────────────┘              │
│       │                                                     │
│       │ 1:1                                                 │
│       ├──────────────────→┌──────────────────────┐          │
│       │                   │ notification_prefs   │          │
│       │                   │──────────────────────│          │
│       │                   │ id (PK)              │          │
│       │                   │ user_id (FK→users)   │←─UNIQUE  │
│       │                   │ email_enabled        │          │
│       │                   │ min_match_score      │          │
│       │                   │ frequency            │          │
│       │                   │ timezone             │          │
│       │                   │ last_processed_at    │          │
│       │                   │ last_digest_sent_at  │          │
│       │                   └──────────────────────┘          │
│       │                                                     │
│       │ 1:N                                                 │
│       ├──────────────────→┌──────────────────────┐          │
│       │                   │ token_blacklist      │          │
│       │                   │──────────────────────│          │
│       │                   │ id (PK)              │          │
│       │                   │ token_jti (UNIQUE)   │          │
│       │                   │ user_id (FK→users)   │          │
│       │                   │ reason               │          │
│       │                   │ blacklisted_at       │          │
│       │                   │ expires_at           │          │
│       │                   └──────────────────────┘          │
│       │                                                     │
└───────┼─────────────────────────────────────────────────────┘
        │
        │ 1:N (multiple tables below)
        │
┌───────┼─────────────────────────────────────────────────────┐
│       │                   JOBS DOMAIN                       │
│       ▼                                                     │
│  ┌──────────┐     N:1     ┌──────────┐                     │
│  │ raw_jobs │←────────────│   jobs   │                     │
│  │──────────│             │──────────│                     │
│  │ id (PK)  │←─FK         │ id (PK)  │                     │
│  │ source   │             │ raw_job_id│ (FK→raw_jobs)      │
│  │ src_job_id│            │ title     │                     │
│  │ payload  │← JSONB      │ title_clean│                   │
│  │ fetched_at│            │ company   │                     │
│  │ processed│             │ description│ (TEXT)             │
│  │ ing_run_id│(FK→ing_runs)│ requirements│ (TEXT)          │
│  │ attempts │             │ respnsblts │ (TEXT)            │
│  └──────────┘             │ loc_city  │                     │
│                           │ loc_country│                    │
│                           │ remote    │                     │
│                           │ uk_country │                    │
│                           │ uk_region │                     │
│                           │ county    │                     │
│                           │ postcode  │                     │
│                           │ latitude  │                     │
│                           │ longitude │                     │
│                           │ workplace │                     │
│                           │ sal_min   │                     │
│                           │ sal_max   │                     │
│                           │ sal_curr  │                     │
│                           │ sal_period│                     │
│                           │ orig_sal  │                     │
│                           │ ann_gbp   │                     │
│                           │ sal_conf  │                     │
│                           │ category  │ (INDEX)            │
│                           │ job_type  │                     │
│                           │ exp_level │                     │
│                           │ posted_at │                     │
│                           │ url       │                     │
│                           │ source    │                     │
│                           │ dedup_hash│ (UNIQUE, INDEX)    │
│                           │ is_active │ (INDEX)            │
│                           │ quality   │                     │
│                           │ search_vec│← TSVECTOR (GIN)    │
│                           │ embedding │← Vector(768)(HNSW) │
│                           │ embed_model│                   │
│                           │ embed_dim │                     │
│                           │ embedded_at│                   │
│                           │ created_at│ (INDEX)            │
│                           │ updated_at│                    │
│                           └─────┬─────┘                    │
│                                 │                           │
│                    ┌────────────┼────────────┐              │
│                    │ 1:N       │ 1:N        │ 1:N          │
│                    ▼           ▼            ▼              │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐     │
│  │  job_skills  │ │ job_postings │ │ recommendations│     │
│  │──────────────│ │──────────────│ │────────────────│     │
│  │ id (PK)      │ │ id (PK)      │ │ id (PK)        │     │
│  │ job_id (FK)  │ │ canonic_id(FK)│ │ user_id (FK)   │     │
│  │ skill (TEXT) │ │ raw_job_id(FK)│ │ job_id (FK)    │     │
│  │ confidence   │ │ source       │ │ match_score    │     │
│  │ is_essential │ │ src_job_id   │ │ rank           │     │
│  │ extract_meth │ │ src_url      │ │ breakdown←JSONB│     │
│  └──────────────┘ │ orig_title   │ │ retrieval_meth │     │
│                   │ orig_desc    │ │ explanation    │     │
│                   │ orig_loc     │ │ run_id (FK)    │     │
│                   │ orig_sal     │ │ created_at     │     │
│                   │ payload←JSONB│ └────────────────┘     │
│                   │ first_seen   │                         │
│                   │ last_seen    │ ┌────────────────┐     │
│                   │ posted_at    │ │  saved_jobs    │     │
│                   │ is_active    │ │────────────────│     │
│                   └──────────────┘ │ id (PK)        │     │
│                                    │ user_id (FK)   │     │
│                                    │ job_id (FK)    │     │
│                                    │ saved_at       │     │
│                                    └────────────────┘     │
│                                                           │
│  ┌────────────────────┐  ┌──────────────────────┐        │
│  │      jobs (cont.)  │  │  recommendation_runs │        │
│  │                    │  │──────────────────────│        │
│  │  user_interactions │  │ id (PK)              │        │
│  │────────────────────│  │ user_id (FK→users)   │        │
│  │ id (PK)            │  │ retrieval_method     │        │
│  │ user_id (FK→users) │  │ candidate_pool_size  │        │
│  │ job_id (FK→jobs)   │  │ final_pool_size      │        │
│  │ interaction_type   │  │ embedding_model      │        │
│  │ metadata ← JSONB   │  │ scoring_config ←JSONB│        │
│  │ source             │  │ latency_ms           │        │
│  │ run_id (FK)        │  │ agent_decisions←JSONB│        │
│  │ created_at         │  │ status               │        │
│  └────────────────────┘  └──────────────────────┘        │
│                                                           │
│  ┌────────────────────┐  ┌──────────────────────┐        │
│  │   notifications    │  │ ingestion_runs       │        │
│  │────────────────────│  │──────────────────────│        │
│  │ id (PK)            │  │ id (PK)              │        │
│  │ user_id (FK→users) │  │ source               │        │
│  │ job_id (FK→jobs)   │  │ started_at           │        │
│  │ type               │  │ finished_at          │        │
│  │ match_score        │  │ records_fetched      │        │
│  │ status             │  │ records_inserted     │        │
│  │ sent_at            │  │ records_skipped      │        │
│  │ dedupe_key (UNIQUE)│  │ errors               │        │
│  │ retry_count        │  │ status               │        │
│  │ created_at         │  └──────────────────────┘        │
│  │ opened             │                                   │
│  └────────────────────┘  ┌──────────────────────┐        │
│                          │  processing_errors    │        │
│  ┌────────────────────┐  │──────────────────────│        │
│  │normalization_aliases│  │ id (PK)              │        │
│  │────────────────────│  │ ing_run_id (FK)      │        │
│  │ id (PK)            │  │ raw_job_id (FK)      │        │
│  │ kind               │  │ error_type           │        │
│  │ alias (UNIQUE+kind)│  │ error_message        │        │
│  │ canonical_value    │  │ stack_trace          │        │
│  │ is_active          │  │ retry_count          │        │
│  └────────────────────┘  │ resolved             │        │
│                          └──────────────────────┘        │
└───────────────────────────────────────────────────────────┘
```

**Vector Storage:**
```
jobs.embedding ──Vector(768)──→ HNSW Index (m=16, ef_construction=64)
                                └── cosine distance via <=> operator

user_profiles.profile_embedding ──Vector(768)──→ No dedicated index
                                                  (compared against jobs.embedding)

jobs.search_vector ──TSVECTOR──→ GIN Index
                                  └── full-text search via @@ operator
```

**Key Relationships:**
- users 1:1 user_profiles
- users 1:1 notification_preferences
- users 1:N recommendations, saved_jobs, notifications, user_interactions, token_blacklist, recommendation_runs
- jobs 1:N job_skills, job_postings, recommendations, saved_jobs, notifications, user_interactions
- raw_jobs 1:N job_postings, processing_errors
- ingestion_runs 1:N raw_jobs, processing_errors
- recommendation_runs 1:N recommendations, user_interactions

---
