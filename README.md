# JobMatch

A job vacancy aggregator and personalised recommendation system. It pulls jobs
from multiple sources, embeds them into a vector space, and matches them against
user profiles using semantic search and a weighted scoring pipeline.

---

## What it does

JobMatch scrapes or imports job listings from Adzuna, Reed, We Work Remotely,
and CSV datasets. Each listing gets normalised (deduplicated, cleaned, scored
for quality) and embedded using a sentence transformer. When a user signs up and
fills in their profile, the system finds the closest jobs in vector space and
ranks them using a blend of semantic similarity, skill overlap, location fit,
salary match, experience level, and recency.

Users can search jobs by keyword or meaning, save favourites, and get a
plain-English explanation of why each job was recommended.

---

## Tech stack

- **Backend API** - FastAPI (Python 3.11+)
- **Frontend** - Flask with Jinja2 templates
- **Database** - PostgreSQL 16 + pgvector extension
- **Embeddings** - BAAI/bge-base-en-v1.5 (768 dimensions)
- **LLM** - Groq API (for explanations and resume parsing)
- **Data sources** - Adzuna API, Reed API, We Work Remotely RSS, CSV uploads

---

## Getting started

### Prerequisites

- Python 3.11+
- Docker (for the database)
- A Groq API key (free at https://console.groq.com/keys)

### Setup

```bash
git clone <your-repo-url>
cd jobmatch

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Database

```bash
docker compose up -d
cp .env.example .env
# Edit .env with your keys
alembic upgrade head
```

### Seed some data

```bash
python -m scripts.seed_csv                  # full dataset
python -m scripts.seed_csv --limit 500      # quick test
```

### Run it

Start the API and the frontend in separate terminals:

```bash
uvicorn app.main:app --reload               # API at http://localhost:8000/docs
python run.py                                # Frontend at http://localhost:5000
```

### Tests

```bash
python -m pytest tests/ -v
```

---

## How the scoring works

When you search for jobs or view recommendations, each job gets a score from
0 to 100 based on these weighted signals:

| Signal | Weight | What it measures |
|---|---|---|
| Semantic similarity | 25% | How close the job and profile are in vector space |
| Skill overlap | 25% | Bidirectional match between your skills and job requirements |
| Location fit | 15% | Whether the job is in your preferred area or remote |
| Salary fit | 15% | How the job's salary range compares to your minimum |
| Experience fit | 10% | Distance between your level and the job's required level |
| Job type fit | 5% | Full-time, contract, etc. match |
| Recency | 5% | How recently the job was posted |

The weights are versioned in `app/services/scoring_config.py` so ablation
studies can compare different configurations.

---

## Admin access

There is no default admin account. To make a user an admin:

1. Register a normal account through the web UI
2. Run this SQL in your database:

```sql
UPDATE users SET is_admin = TRUE WHERE email = 'your@email.com';
```

Admins can access `/admin/` routes to manage jobs, run reprocessing, and
view ingestion logs.

---

## Notifications

The notification scheduler runs as a separate process:

```bash
python -m scripts.run_scheduler
```

Set `SCHEDULER_ENABLED=true` only for that process. It respects each user's
frequency preference (instant, daily, weekly) and sends emails through SMTP.
SMTP needs to be configured in `.env` for emails to actually send.

---

## Configuration

Key settings in `.env`:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Flask session secret
- `GROQ_API_KEY` - For LLM explanations and resume parsing
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email delivery
- `SCHEDULER_ENABLED` - Enable the notification scheduler
- `PASSWORD_RESET_EXPIRY_MINUTES` - Reset link lifetime (default: 15)

---

## Project structure

```
app/                    FastAPI backend
  agents/               Recommendation pipeline
  api/                  API endpoints
  core/                 Auth, security
  ingestion/            Data source connectors
  models/               SQLAlchemy models
  processing/           Normalisation, dedup, salary parsing
  services/             Embedding, search, scoring, explanations
alembic/                Database migrations
scripts/                One-off and operational scripts
tests/                  Pytest test suite
webapp/                 Flask frontend
  routes/               View functions
  templates/            Jinja2 HTML templates
```
