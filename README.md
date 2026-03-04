# GitLense — AI Codebase Intelligence

> Ask questions about any GitHub repository in plain English. GitLense indexes your codebase, understands its structure, and answers technical questions with cited sources.

![Overall RAG Score: 0.906](https://img.shields.io/badge/RAG%20Score-0.906-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.134-green)

---

## What It Does

1. Paste a GitHub URL
2. GitLense clones, parses, and embeds the entire codebase
3. Ask anything — "How does auth work?", "Where are the routes?", "What does this repo do?"
4. Get accurate answers with file citations

---

## Architecture

```
User → FastAPI → Redis → Celery Worker
                              ↓
                   Clone repo → Parse with LanguageParser
                              ↓
                   Embed with OpenAI → Store in Qdrant
                              ↓
User asks question → Query Expansion → Qdrant Search (top-20)
                              ↓
                   Cohere Rerank (top-5) → GPT-4o → Answer + Sources
```

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite (Netlify) |
| Backend | FastAPI (Railway) |
| Task Queue | Celery + Redis (Railway) |
| Vector DB | Qdrant Cloud |
| Metadata DB | MongoDB Atlas |
| Embeddings | OpenAI text-embedding-3-small |
| Reranker | Cohere rerank-english-v3.0 |
| LLM | GPT-4o |

---

## RAG Pipeline Quality

Evaluated on 20 questions using [Ragas](https://ragas.io):

```
faithfulness           0.801  ████████████████      (no hallucination)
answer_relevancy       0.916  ██████████████████    (answers the question)
context_precision      0.906  ██████████████████    (retrieves right chunks)
context_recall         1.000  ████████████████████  (finds all needed context)

Overall Score          0.906
```

---

## Project Structure

```
gitlense-api/
├── main.py                  # FastAPI app, CORS, routers
├── config.py                # Pydantic settings from .env
├── routers/
│   ├── auth.py              # Register, login, logout
│   ├── repos.py             # Ingest, status, list, delete
│   └── chat.py              # RAG query endpoint
├── services/
│   ├── auth.py              # JWT + bcrypt
│   ├── parser.py            # LanguageParser + chunking
│   ├── embedder.py          # OpenAI embeddings → Qdrant
│   ├── qdrant.py            # Vector search + index management
│   ├── rag.py               # Query expansion + answer generation
│   ├── rerank.py            # Cohere reranking
│   └── github.py            # GitHub API + git clone
├── worker/
│   ├── celery_app.py        # Celery config
│   └── tasks.py             # ingest_repo task
├── models/
│   ├── user.py
│   └── repo.py
└── scripts/
    ├── generate_golden_dataset.py   # Synthetic Q&A generation
    └── evaluate.py                  # Ragas evaluation
```

---

## Local Development

### Prerequisites
- Python 3.12
- Redis running locally
- MongoDB Atlas account
- Qdrant Cloud account
- OpenAI API key
- Cohere API key

### Setup

```bash
# clone
git clone https://github.com/bhatraasim/gitlense-api
cd gitlense-api

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install dependencies
uv sync

# copy env file
cp .env.example .env
# fill in your values
```

### Environment Variables

```env
# MongoDB
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=gitlense

# Qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_key
QDRANT_COLLECTION=code_chunks

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o

# Cohere
COHERE_API_KEY=your_key

# Auth
JWT_SECRET_KEY=your_secret

# CORS
FRONTEND_URL=http://localhost:5173
```

### Running Locally

```bash
# terminal 1 — start redis
using docker compose

# terminal 2 — start FastAPI
uv run fastapi dev main.py

# terminal 3 — start Celery worker
uv run celery -A worker.celery_app worker --loglevel=info --pool=solo
```

API docs available at: `http://localhost:8000/docs`

### First Time Setup

After deleting the Qdrant collection, recreate the index:
```bash
# first ingest a repo via the API, then run:
uv run python -c "from services.qdrant import create_indexes; create_indexes()"
```

---

## Docker

```bash
docker compose up
```

---

## Evaluation

Generate a golden dataset and run Ragas evaluation:

```bash
# generate Q&A pairs from an ingested repo
uv run python scripts/generate_golden_dataset.py --repo_id <repo_id>

# run evaluation (costs ~$0.10)
uv run python scripts/evaluate.py --repo_id <repo_id> --sample 20
```

---

## API Reference

See [API_DOCS.md](./API_DOCS.md) for complete endpoint documentation.

---

## Deployment

Deployed on Railway with 3 services:

| Service | Start Command |
|---------|--------------|
| `gitlens` | `uv run fastapi run main.py --host 0.0.0.0 --port 8000` |
| `gitlens-worker` | `uv run celery -A worker.celery_app worker --loglevel=info --pool=solo` |
| `Redis` | Railway managed |