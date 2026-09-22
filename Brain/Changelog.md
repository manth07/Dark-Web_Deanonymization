# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Every PR that changes a contract (schema, API, folder structure) adds an
entry here in the same PR — this is enforced by `Master_rules.md` §5
(Definition of Done).

## [Unreleased]

### ai-graph
- Added: `docker-compose.yml` multi-container orchestration for `neo4j:5.20-community`, `ollama:latest`, and `stylometry-engine`.
- Added: Production/dev `Dockerfile` for `stylometry-engine` on `python:3.11-slim` with pre-cached spaCy `en_core_web_sm` and NLTK `punkt`/`punkt_tab`/`stopwords`.
- Added: Pinned `requirements.txt` with spaCy, NLTK, Neo4j, Ollama, Pydantic v2, pytest, and scikit-learn.
- Added: `.env.example`, `.env`, `.gitignore`, and `.dockerignore`.
- Added: Pydantic v2 schemas in `schemas/raw_post.py` (`RawForumPost`) and `schemas/extracted_features.py` (`StylometricFeatures`, `ExtractedIdentifiers`, `CryptoWallet`, `ThreatActorProfile`).
- Added: Configuration manager `core/config.py` (and root alias `config.py`) using `pydantic-settings` with default values and validation bounds.
- Added: Structured JSON logger in `core/logger.py` conforming to `Error_Handling.md`.
- Added: Unit test suite `tests/test_schemas.py` validating schema serialization, deserialization, aliasing, and validation constraints.
- Added: Synthetic dark web forum dataset generator in `fixtures/synthetic_generator.py` modeling 4 distinct persona archetypes across 3 simulated dark web forums.
- Added: Synthetic corpus `fixtures/sample_posts.json` (24 posts) and mirrored to `data/sample_texts.json`.
- Added: Shared pytest fixtures in `conftest.py` for raw and Pydantic post models.
- Added: Integration tests in `tests/test_fixtures.py` verifying stylistic overlap between Persona A (`ShadowBroker`) and Persona C (`GhostMigrant`).
- Added: Classical stylometric feature extraction engine `nlp/stylometry.py` (`StylometryExtractor`) calculating lexical, syntactic, and structural markers.
- Added: Robust edge case protection handling empty texts, single words, emojis, and non-English text.
- Added: Unit test suite `tests/test_stylometry.py` validating feature variance between clipped and academic text.
- Added: Identifier extraction engine `nlp/identifier_extractor.py` (`IdentifierExtractor`) for Bitcoin (P2PKH, P2SH, Bech32), Monero (standard, integrated), Ethereum, PGP blocks/fingerprints, and public IPv4 indicators.
- Added: Subnet filtering for IPv4 eliminating RFC 1918 private and loopback noise.
- Added: Unit test suite `tests/test_identifiers.py` validating multi-currency, PGP, and IP indicator harvesting.
- Added: Local AI embedding and stylometric service `ai/ollama_client.py` (`OllamaStylometryService`) connecting to Ollama with retry policies.
- Added: Bias-stripping pre-processor removing wallets, PGP, and URLs prior to vector generation.
- Added: Cosine similarity calculation module with boundary and zero-vector safety.
- Added: Deterministic L2-normalized pseudo-random mock vector generator for offline unit testing (`MOCK_OLLAMA=true`).
- Added: Unit test suite `tests/test_ollama_service.py` validating embedding dimensions, similarity edge cases, and daemon offline fallback.
- Added: Multi-factor entity resolution and persona linkage engine `ai/entity_resolution.py` (`EntityResolver`, `LinkageDecision`) combining hard cryptographic identifiers with dense AI embeddings and classical stylometric variance.
- Added: Canonical threat actor cluster resolution with explainable evidence trails (`link_reasons`).
- Added: Unit test suite `tests/test_entity_resolution.py` confirming cross-marketplace linkage between Persona A (`ShadowBroker`) and Persona C (`GhostMigrant`) with confidence >= 0.80.
- Added: Thread-safe Neo4j driver connection manager `graph/driver.py` with connection pooling, retries, and graceful context manager teardown.
- Added: Schema migration runner `graph/schema.py` enforcing 6 unique/node-key constraints and 3 B-tree indexes idempotently with zero duplicate errors.
- Added: Unit test suite `tests/test_graph_schema.py` verifying DDL syntax, driver lifecycle, and idempotency handling.
- Added: Idempotent graph ingestion repository `graph/repository.py` (`ThreatGraphRepository`) supporting `upsert_persona`, `create_attribution_link`, `query_actor_network`, and candidate profile queries with offline in-memory fallback.
- Added: Integration test suite `tests/test_graph_repository.py` validating full threat graph topology, node upserts, Cypher query dispatch, and idempotency.
- Added: Core processing pipeline in `pipeline.py` (`StylometryPipeline`) integrating classical NLP stylometry, identifier extraction, Ollama vector embeddings, graph candidate queries, entity resolution, and graph persistence.
- Added: Intelligence reporter `export/reporter.py` (`IntelligenceReporter`) generating deep NTRO JSON deliverables, analyst CSV spreadsheets, and human-readable briefings.
- Added: Command line interface `main.py` powered by Typer and Rich with commands `init-db`, `ingest-fixtures`, `export-actor`, and `run-worker`.
- Added: Unit and integration test suite `tests/test_pipeline.py` validating end-to-end pipeline processing, persona linking, and CLI execution.
- Added: Full end-to-end integration and verification suite `tests/test_e2e_pipeline.py` confirming cross-marketplace persona resolution, NTRO deliverable JSON schema compliance, analyst CSV spreadsheet mapping, and executive threat briefing narrative formatting.
- Added: GitHub Actions automated CI workflow `.github/workflows/ai-graph.yml` running containerized Neo4j service healthcheck and full 51-test suite.
- Added: Comprehensive project `README.md` with system architecture, capabilities, quickstart, CLI usage, and test matrix.

### backend
- _(nothing yet)_

### scraper
- _(nothing yet)_

### frontend
- _(nothing yet)_

---

## How to add an entry

```
### <folder>
- Added: <what>
- Changed: <what, and why — esp. if it's a schema/contract change>
- Fixed: <what>
```

## [0.1.0] — Project scaffold
- Initial four-folder repo structure created (`/frontend`, `/backend`,
  `/scraper`, `/ai-graph`).
- Docs baseline established (this file set).
