<!-- PROJECT LOGO -->
<div align="center">

<p>
  <img src="docs/assets/project_logo.png"
  alt="FDA Recall RAG" width="100px"/>
</p>

<!-- Header -->
<h1 align="center">FDA Recall & Compliance Assistant</h1>

![CI](https://github.com/seb-sto/fda-recall-rag/actions/workflows/ci.yml/badge.svg)
![](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)
![](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff)
![](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff)
![](https://img.shields.io/badge/ChromaDB-2E2E2E)
![](https://img.shields.io/badge/Anthropic_Claude-D97757?logo=anthropic&logoColor=fff)
![](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff)
![](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

</div>


A retrieval-augmented question-answering system over real FDA data — 21 CFR regulations (Parts 7, 117, 211, 820) and openFDA food/drug/device enforcement (recall) records. Every document in the vector store traces back to a real regulation or a real recall; nothing is synthetic. Ask a compliance question and get a cited answer, backed by cross-encoder reranking and a citation-enforcing system prompt that's measurably resistant to fabrication.

---

## Architecture

<!-- TODO: architecture diagram — eCFR + openFDA → ingestors → ChromaDB (4 collections) → retrieval + reranking → Claude → FastAPI → Streamlit -->

Pipeline: **eCFR API + openFDA API** → **ingestors** (`IngestorBase` pattern, shared `fetch()`/`parse()`/`to_documents()` interface) → **chunking** (`RecursiveCharacterTextSplitter`, clause-aware) → **local embeddings** (`all-MiniLM-L6-v2`) → **4 ChromaDB collections** (`regulations`, `food_recalls`, `drug_recalls`, `device_recalls`) → **retrieval + metadata filtering + cross-encoder reranking** → **Claude** (citation-enforcing system prompt) → **FastAPI** (auth, rate limiting, structured logging, conversation memory) → **Streamlit** chat UI.

See [`docs/design-decisions.md`](docs/design-decisions.md) for the reasoning behind each of these choices, and [`docs/evaluation.md`](docs/evaluation.md) for measured retrieval/generation quality (RAGAS-style, hand-rolled).

## Screenshots

<!-- TODO: capture a real Streamlit conversation once the UI is finalized -->

---

## Quickstart

### Prerequisites

- Docker Desktop
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### 1. Clone and configure

```bash
git clone https://github.com/seb-sto/fda-recall-rag.git
cd fda-recall-rag
cp .env.example .env
# Fill in CLAUDE_API_KEY, OPENFDA_API_KEY, and choose your own API_KEY in .env
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Start the full stack

```bash
docker-compose up --build
```

This builds and starts ChromaDB, the FastAPI service, and the Streamlit UI together.

| Service   | URL                     |
|-----------|-------------------------|
| Streamlit | http://localhost:8501   |
| API       | http://localhost:8000   |
| ChromaDB  | http://localhost:8001   |

### 4. Run ingestion once

The vector store starts empty. Populate it (one-time, or whenever you want to refresh the source data):

```bash
uv run python -m src.ingestion.run
uv run python -m src.embedding.run
```

### 5. Ask a question

Open http://localhost:8501 and ask something like *"What is a Class II recall?"* — you should get a cited answer (e.g. `[21 CFR § 7.3]`) with sources and rerank scores shown alongside it.

---

## Tech Stack

| Layer               | Technology                                  |
|----------------------|---------------------------------------------|
| API                  | FastAPI + Uvicorn                           |
| UI                   | Streamlit                                   |
| Vector store         | ChromaDB (4 collections)                    |
| Embeddings           | sentence-transformers (`all-MiniLM-L6-v2`, local) |
| Reranking            | cross-encoder (`ms-marco-MiniLM-L-6-v2`, local) |
| Generation           | Claude (Haiku default, Sonnet configurable via `LLM_MODEL`) |
| Chunking             | LangChain text splitters                    |
| Auth / rate limiting | Custom API-key dependency + `slowapi`       |
| Logging              | `structlog`, request-ID propagation         |
| Evaluation           | Hand-rolled RAGAS-style metrics, Claude Sonnet as judge |
| Containers           | Docker Compose                              |
| CI/CD                | GitHub Actions (`ruff`, `mypy`, `pytest`)   |
| Package management   | uv                                           |

---

## Data Sources

### eCFR API — Title 21 (Food and Drugs)
- **URL:** https://www.ecfr.gov/api/versioner/v1/
- **Parts covered:** 7 (Enforcement Policy / Recalls), 117 (Food CGMP), 211 (Drug CGMP), 820 (Device Quality Management System Regulation)
- **Coverage:** current regulation text as of a given date
- **Download:** automated via `ECFRIngestor`

### openFDA — Food, Drug, and Device Enforcement
- **URL:** https://api.fda.gov/{food,drug,device}/enforcement.json
- **Coverage:** ~87,000 recall records across all three product types (2004–present, updated weekly)
- **Download:** automated via `OpenFDAEnforcementIngestor`, one instance per product type

> **Note on pagination:** openFDA hard-caps `skip`-based pagination at 25,000 records — two of the three collections (food: ~29K, device: ~40K) exceed that. The ingestor uses openFDA's `search_after`/`Link`-header pagination instead, which has no such limit.

---

## Repository Structure

```
fda-recall-rag/
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .env.example
├── Makefile
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── src/
│   ├── ingestion/
│   │   ├── base.py           # IngestorBase: fetch()/parse()/to_documents()
│   │   ├── ecfr.py           # eCFR XML ingestor
│   │   ├── openfda.py        # openFDA enforcement ingestor (food/drug/device)
│   │   └── run.py            # runs all ingestors, writes data/processed/*.jsonl
│   ├── embedding/
│   │   ├── chunk.py          # chunking + stable chunk-ID scheme
│   │   ├── embed.py          # sentence-transformers wrapper
│   │   ├── store.py          # ChromaDB client + idempotent upsert
│   │   └── run.py            # chunk → embed → upsert, for all 4 collections
│   ├── rag/
│   │   ├── retrieve.py       # multi-collection retrieval + metadata filtering
│   │   ├── rerank.py         # cross-encoder reranking
│   │   ├── generate.py       # Claude client, citation-enforcing prompt
│   │   └── memory.py         # per-session conversation history
│   ├── api/
│   │   ├── main.py           # FastAPI app: /health, /query, /documents
│   │   ├── auth.py           # API-key dependency
│   │   ├── schemas.py        # Pydantic request/response models
│   │   └── logging_config.py # structlog setup
│   ├── ui/
│   │   └── app.py            # Streamlit chat interface
│   └── eval/
│       ├── metrics.py        # hand-rolled RAGAS-style metrics (Claude judge)
│       └── run_eval.py       # baseline vs. reranked evaluation harness
├── tests/                    # pytest suite, LLM calls mocked
├── data/
│   ├── raw/                  # sample API responses
│   ├── processed/            # ingested {text, metadata} JSONL, one file per collection
│   └── eval/
│       └── test_set.jsonl    # 36 hand-written, source-grounded Q&A pairs
├── docs/
│   ├── evaluation.md         # methodology + baseline vs. reranked results
│   ├── design-decisions.md   # trade-offs and why
│   ├── data-dictionary.md    # metadata schema per collection
│   └── assets/
│       └── cited-answer-mark.png
└── .github/
    └── workflows/
        └── ci.yml             # ruff, mypy, pytest — no secrets required
```

---

## What I Learned

- **Chunk size has to be validated against real length distributions, not assumed** — `all-MiniLM-L6-v2` silently truncates anything past 256 tokens (~1,000–1,300 characters), with no error. Measuring the actual data before choosing a chunk size showed the *median* regulation section was already past that limit — meaning more than half of the regulatory text would have been silently cut before embedding if chunking had been skipped or sized casually. Recall records, by contrast, mostly fit in a single chunk untouched. The right chunking strategy depended on the data's real shape, not a one-size default.

- **Semantic search alone fails on the exact things a compliance user would actually ask about** — a real recall (CytoDetox, a dietary supplement) was in the vector store but didn't surface for "why was CytoDetox recalled?" because its brand name is a rare token with a poor embedding representation; the query matched more generic, topically-similar recalls instead. Fixed with a hybrid exact-match filter (Chroma's `where_document`) layered on top of vector search — proper nouns and IDs need lexical matching that pure embeddings don't reliably provide.

- **Cross-encoder reranking catches confusions that embedding distance can't see** — a device-classification section (21 CFR § 820.10, about medical device *risk categories*) ranked highly for a *recall*-classification question, purely because both use "Class I/II/III" phrasing. Embedding similarity can't tell these two unrelated regulatory concepts apart; a cross-encoder — which reads the query and candidate together instead of comparing precomputed vectors — scored that same chunk near the bottom of the reranked list, confirming two-stage retrieval earns its extra cost on cases exactly like this one.

- **Government API metadata is messier than it looks, and filters need to degrade gracefully, not assume clean structure** — openFDA's `distribution_pattern` field is free text, not a structured list, and its formatting is inconsistent across records. A state filter built on the assumption of clean, delimited data would have silently mismatched real records; the actual filter treats it as best-effort substring matching instead of pretending the field is more structured than it is.

- **A citation-enforcing system prompt has a measurable effect** — Initial evaluation showed faithfulness and answer relevancy staying high and roughly flat (~0.75, ~0.97) whether or not reranking was enabled, while reranking's real, measurable effect concentrated exactly where it should: context precision (+17%) and context recall (+4.4%). The generation layer correctly avoided fabricating answers even when retrieval brought in partially irrelevant chunks — a testable claim, not an assumption.