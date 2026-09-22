# Phases

Each phase lists goal → tasks → exit criteria. `/ai-graph` phases are
detailed; other folders' phases are noted where they gate an integration
point.

## Phase 0 — Environment Setup
**Goal:** everyone can run the local stack.
- Repo scaffold with four folders + docs (this set).
- `docker-compose.yml` skeleton: `neo4j`, `ollama` services running.
- Pull a model into Ollama (`ollama pull llama3` or `qwen2.5`) and confirm
  `ollama list` shows it.
- Confirm Neo4j browser reachable at `localhost:7474`.
**Exit:** `docker compose up -d neo4j ollama` works clean on a fresh machine.

## Phase 1 — Schema & Sample Data
**Goal:** the contract is real before any pipeline code exists.
- Finalize `Data_model.md` node/relationship schema.
- Run the Cypher constraint/index setup against local Neo4j.
- Write `data/sample_texts.json` with planted persona pairs (same style,
  different handle) for entity-resolution testing.
**Exit:** constraints applied; sample data reviewed against
`Scraping_spec.md`'s schema.

## Phase 2 — Feature Extraction Pipeline
**Goal:** raw text → stylometric feature vector.
- Sentence length distribution, punctuation frequency, n-gram extraction
  (spaCy/NLTK).
- Unit tests per feature type (`Testing.md` §2).
**Exit:** `features/` module fully unit-tested against sample fixtures.

## Phase 3 — Embeddings & Similarity
**Goal:** feature vectors → embeddings → cosine similarity scores.
- Ollama client wrapper with timeout/retry (`Error_Handling.md`).
- Cosine similarity function + threshold tuning against planted pairs in
  `sample_texts.json`.
**Exit:** planted persona pairs score above threshold; unrelated pairs score
below it.

## Phase 4 — Neo4j Ingestion Layer
**Goal:** profiles + wallets + infra indicators land in the graph correctly.
- `graph/` module: parameterized Cypher writers for all node/relationship
  types in `Data_model.md`.
- Idempotent `MERGE`-based upserts (no duplicate actor nodes on reprocessing).
**Exit:** integration tests (`Testing.md` §2, Neo4j section) pass.

## Phase 5 — Entity Resolution Logic
**Goal:** turn similarity scores into actual persona links with confidence.
- Cluster handles above the similarity threshold into `PersonaCluster` /
  `SAME_PERSONA_AS` edges.
- Aggregate `attribution_confidence` per `Data_model.md` §3's weighting.
**Exit:** `test_entity_resolution_recovers_known_pairs()` passes end-to-end.

## Phase 6 — Cross-Folder Integration
**Goal:** swap dummy data for the real pipeline boundary.
- Consume actual `scraper` output (same schema, real records).
- `backend` confirmed reading the graph correctly for dashboard queries.
**Exit:** one real end-to-end run: scraper → ai-graph → Neo4j → backend API
returns expected actor profile.

## Phase 7 — Polish & Demo Prep
**Goal:** repeatable, explainable demo.
- Curate a demo query set (timeline filter, confidence filter, persona
  rebrand example).
- Confirm CSV/JSON/report export works end-to-end.
- Dry-run the full pipeline from a clean `docker compose up`.
- Prepare the "why did this merge happen" explanation path (evidence list on
  `SAME_PERSONA_AS`, per `Data_model.md` §3) for judge Q&A.
**Exit:** full demo runs clean, twice, from a fresh clone.
