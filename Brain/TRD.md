# TRD — Technical Requirements Document

## 1. System Overview

Four modules, one repo, isolated folders:

```
scraper  --> raw records (JSON) --> ai-graph --> Neo4j graph --> backend API --> frontend dashboard
```

## 2. Module Tech Stack

| Module | Stack |
|---|---|
| scraper | Tor client/proxy, Python (requests/Scrapy or similar), infra fingerprint checks |
| ai-graph | Python, spaCy/NLTK, Ollama (Llama 3 / Qwen, local), scikit-learn/numpy (cosine sim), neo4j Python driver |
| backend | REST API (framework per backend owner's choice), export generation, query orchestration |
| frontend | Dashboard/GUI, timeline filters, actor detail views |

## 3. Data Flow

1. `scraper` collects raw text + page metadata from marketplaces/forums/hidden
   services, writes records matching the schema in `Scraping_spec.md`.
2. `ai-graph` consumes raw records:
   - extracts stylometric features (sentence length, punctuation frequency,
     n-grams),
   - generates embeddings via local Ollama model,
   - computes cosine similarity for entity resolution,
   - writes actor/identifier/infra nodes and relationship edges to Neo4j
     (see `Data_model.md`).
3. `backend` queries Neo4j, exposes REST endpoints for the dashboard, and
   generates CSV/JSON/report exports.
4. `frontend` renders actor profiles, relationship graph views, and timeline
   queries against the backend API.

## 4. Interfaces

- **scraper → ai-graph:** JSON record schema, see `Scraping_spec.md` and
  `API_Contracts.md`.
- **ai-graph → backend:** the Neo4j graph itself is the contract (schema in
  `Data_model.md`); backend reads directly via the Neo4j driver, never writes
  actor/identity nodes.
- **backend → frontend:** REST API, versioned, documented in
  `API_Contracts.md`.

## 5. Infrastructure (local, via Docker Compose)

| Service | Purpose |
|---|---|
| `neo4j` | Graph store |
| `ollama` | Local LLM inference (embeddings) |
| `raw-store` (Mongo/Postgres, or filesystem for hackathon scale) | Scraper output landing zone |
| `backend` | API service |
| `frontend` | Dashboard |
| `tor-proxy` | Used only by `scraper` — no other service reaches Tor |

## 6. Non-Functional Requirements

- **Security:** see `Security.md` — no plaintext secrets, network-isolated
  Tor egress, authenticated Neo4j.
- **Performance:** dashboard queries < 2s on demo-scale graph (~10k nodes).
- **Autonomy:** scraper + ai-graph pipeline runnable on a schedule without
  manual intervention (cron or simple scheduler is sufficient for prototype).
- **Portability:** entire stack runs via `docker compose up` on a judge's
  laptop with no external API keys.

## 7. Out of Scope

- Horizontal scaling / distributed crawling.
- Production-grade authn/authz (basic auth acceptable for demo).
