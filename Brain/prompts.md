> **Role Target:** AI Stylometry & Neo4j Engine Developer  
> **Mission:** Build an autonomous, containerized NLP stylometry and Neo4j graph intelligence engine to deanonymize dark web threat actors via stylistic fingerprinting and identity resolution.  
> **How to Use:** Execute these prompts sequentially inside your AI code editor (Cursor, Windsurf, Claude Code, or Aider). Do not move to the next loop prompt until the acceptance criteria and tests of the current loop pass.

You are an expert Python, NLP, and Graph Database Engineer working on an NTRO threat actor deanonymization system.
You adhere to test-driven, loop-engineered development.

Core Guidelines:
1. Tech Stack: Python 3.11+, Ollama API (Llama 3 / Qwen2.5-Coder), NLTK, spaCy, Neo4j 5+ (official Python driver), Pydantic v2, Pytest, Docker & Docker Compose.
2. Architecture: Maintain strict separation of concerns:
   - `core/`: Configurations and base logging.
   - `nlp/`: Classical stylometric extraction and regex identifier parsing.
   - `ai/`: Local Ollama vector generation and cosine similarity calculation.
   - `graph/`: Neo4j driver, schema migrations, and parameterized Cypher queries.
   - `fixtures/`: Synthetic dark web dataset generator for offline testing.
3. Code Quality: Fully type-annotated (`mypy` compliant), docstrings on public methods, 0 hardcoded credentials, idempotent Cypher queries (`MERGE`).
4. Independence: The module must run 100% autonomously on synthetic fixtures without relying on external live scrapers.


Loop 1: Infrastructure & Container Orchestration
Prompt 1.1 — Docker Compose & Multi-Container Setup
Task: Create the multi-container development environment for the Stylometry & Neo4j engine.

1. Create a `docker-compose.yml` file defining three services:
   - `neo4j`:
     - Image: neo4j:5.20-community
     - Environment: NEO4J_AUTH=neo4j/ThreatIntelSecurePass2026, NEO4J_PLUGINS=["apoc"]
     - Ports: 7474:7474 (Browser), 7687:7687 (Bolt)
     - Volumes: neo4j_data:/data
     - Healthcheck verifying port 7687 is accepting connections.
   - `ollama`:
     - Image: ollama/ollama:latest
     - Ports: 11434:11434
     - Volumes: ollama_models:/root/.ollama
     - Healthcheck to verify http://localhost:11434/api/tags.
   - `stylometry-engine`:
     - Build: Context `.`, Dockerfile `Dockerfile`
     - Depends on `neo4j` and `ollama` with `condition: service_healthy`
     - Environment variables loaded from `.env`
     - Volume mount for local code development.

2. Create `Dockerfile` for `stylometry-engine`:
   - Base: python:3.11-slim
   - Install system dependencies (build-essential, curl).
   - Install Python dependencies via requirements.txt.
   - Download the spaCy model `en_core_web_sm` and NLTK packages (`punkt`, `stopwords`).

3. Create `.env.example` containing default configs for Neo4j and Ollama.

Acceptance Criteria:
- Running `docker compose config` validates without errors.
- Dockerfile builds cleanly with pre-downloaded NLP language models.

Loop 2: Configuration, Data Models & Synthetic Test Fixture
Prompt 2.1 — Settings & Pydantic Data Contracts
Task: Implement the configuration module and Pydantic schemas representing scraped dark web posts and extracted threat actor artifacts.

1. Implement `config.py` using `pydantic-settings`:
   - Neo4j URI (`bolt://localhost:7687`), username, password, database name.
   - Ollama Base URL (`http://localhost:11434`), embedding model name (`nomic-embed-text` or `qwen2.5:7b`), LLM stylometry model (`qwen2.5:7b` or `llama3:8b`).
   - Stylometry thresholds: cosine similarity linkage threshold (default: 0.82).

2. Implement `schemas/raw_post.py`:
   - Model `RawForumPost`: post_id, forum_name, author_handle, raw_content, timestamp, thread_title, source_url.

3. Implement `schemas/extracted_features.py`:
   - Model `StylometricFeatures`:
     - Lexical: average_sentence_length, average_word_length, type_token_ratio, hapax_legomena_ratio.
     - Syntactic: punctuation_frequency (dict of char counts), pos_tag_distribution (dict), function_word_frequency (dict).
     - Structural: paragraph_count, uppercase_ratio, character_count.
     - Vectors: embedding (list of floats).
   - Model `ExtractedIdentifiers`:
     - crypto_wallets: list of dicts with `currency` (BTC, XMR, ETH) and `address`.
     - pgp_keys: list of PGP key blocks or key IDs.
     - ip_addresses: list of extracted IPv4/IPv6 indicators.
   - Model `ThreatActorProfile`:
     - handle: str
     - platform: str
     - features: StylometricFeatures
     - identifiers: ExtractedIdentifiers
     - attribution_id: Optional[str]

Acceptance Criteria:
- Unit tests in `tests/test_schemas.py` validate schema serialization, deserialization, and field constraints.

Prompt 2.2 — Synthetic Dark Web Corpus Generator (Independence Strategy)
Task: Create a synthetic fixture generator that allows development and testing without access to live dark web scrapers.

1. Create `fixtures/synthetic_generator.py`:
   - Generate realistic forum messages across 3 simulated dark web forums (e.g., "DreadClone", "BreachNode", "AlphaVendor").
   - Include 4 distinct persona archetypes with planted stylometric habits:
     - Persona A ("ShadowBroker"): Short clipped sentences, frequent ellipses ("..."), heavy capitalization, Bitcoin wallet (P2PKH/Bech32), PGP signature.
     - Persona B ("CryptoRebel"): Long verbose academic style, excessive semicolons, Monero (XMR) addresses, custom jargon.
     - Persona C ("GhostMigrant"): Deliberately mimic Persona A's writing style under a different handle on a different marketplace to test entity resolution.
     - Persona D ("ScriptKiddie"): Poor punctuation, repetitive slang, Ethereum addresses, clearnet IP leakage.
   - Generate at least 20 raw post records matching `RawForumPost`.

2. Save the output to `fixtures/sample_posts.json`.
3. Add a CLI command or pytest fixture in `conftest.py` providing seamless access to these posts.

Acceptance Criteria:
- `fixtures/sample_posts.json` is generated with valid schema structures.
- Running `pytest tests/test_fixtures.py` verifies at least 2 personas have overlapping stylistic traits and distinct handles.


Loop 3: Feature Extraction & Identifier Harvester
Prompt 3.1 — Classical Stylometric Feature Extractor
Task: Build the classical NLP stylometry extraction engine using NLTK and spaCy.

1. Create `nlp/stylometry.py` with class `StylometryExtractor`:
   - Method `extract_features(text: str) -> StylometricFeatures`:
     - Tokenize sentences and words using spaCy/NLTK.
     - Lexical:
       - Calculate mean sentence length (word count per sentence).
       - Calculate mean word length (character count per word).
       - Calculate Type-Token Ratio (TTR: unique words / total words).
       - Calculate Yule's K characteristic or Hapax Legomena ratio (words appearing once / total words).
     - Syntactic:
       - Calculate frequency of punctuation marks: `!`, `?`, `...`, `,`, `;`, `:`, quotes, brackets.
       - Extract Part-of-Speech (POS) tags distribution (proportion of nouns, verbs, adjectives, adverbs).
     - Structural:
       - Uppercase letter ratio (uppercase chars / total chars).
       - Formatting indicators (indentations, bullet points, newline frequency).
     - Return a populated `StylometricFeatures` Pydantic model (embedding field left empty for AI loop).

2. Handle edge cases: empty strings, pure ASCII/non-English text, extremely short strings (< 10 words) by providing normalized default values.

Acceptance Criteria:
- Unit tests in `tests/test_stylometry.py` confirm distinct feature values between clipped writing and academic writing.
- Zero crashes on edge cases (empty text, single word, long garbage strings).

Prompt 3.2 — Identifier Extraction Engine (Wallets, PGP, IPs)
Task: Create high-precision regex and heuristic extractors for cryptocurrency wallets, PGP fingerprints, and IP indicators.

1. Create `nlp/identifier_extractor.py` with class `IdentifierExtractor`:
   - Method `extract_all(text: str) -> ExtractedIdentifiers`:
     - Bitcoin (BTC):
       - Legacy P2PKH (starts with `1`, length 26-35)
       - P2SH (starts with `3`, length 34)
       - Bech32 (starts with `bc1`, alphanumeric)
     - Monero (XMR):
       - Standard address (starts with `4`, 95 characters)
       - Integrated address (starts with `8`, 106 characters)
     - Ethereum (ETH):
       - Starts with `0x`, 40 hex characters
     - PGP Keys / Fingerprints:
       - Match `-----BEGIN PGP PUBLIC KEY BLOCK-----...-----END PGP PUBLIC KEY BLOCK-----`
       - Match 40-character hex PGP fingerprints.
     - IP Addresses:
       - Extract IPv4 addresses (exclude private/loopback ranges like 127.0.0.1, 10.0.0.0/8, 192.168.0.0/16 unless explicitly flagged).

2. Validate all crypto regex patterns against known valid/invalid checksum formats where feasible.

Acceptance Criteria:
- Unit tests in `tests/test_identifiers.py` verify extraction of BTC, XMR, ETH, PGP blocks, and IPv4 addresses embedded in typical forum posts.


Loop 4: Ollama Stylometric Embeddings & Entity Resolution
Prompt 4.1 — Ollama Client & Vector Embedding Pipeline
Task: Implement the local AI embedding and stylometric semantic profiling service using Ollama.

1. Create `ai/ollama_client.py` with class `OllamaStylometryService`:
   - Initialize connection to Ollama using `httpx` with timeout and retry policies.
   - Method `generate_embedding(text: str, model: str = "nomic-embed-text") -> list[float]`:
     - Pre-process text to remove overt bias identifiers (strip wallet addresses, usernames, and explicit URLs so the embedding focuses purely on writing style and tone).
     - Request vector embeddings from Ollama's `/api/embeddings` endpoint.
   - Method `compute_similarity(vec_a: list[float], vec_b: list[float]) -> float`:
     - Calculate cosine similarity between two feature/embedding vectors.
   - Method `generate_stylistic_profile_summary(text_samples: list[str]) -> str`:
     - Prompt Ollama (Qwen2.5 or Llama 3) to summarize the persona's tone, vocabulary habits, syntax quirks, and technical sophistication.

2. Implement a mock/fallback mode when Ollama is unreachable during unit tests (`MOCK_OLLAMA=true`) returning deterministic normalized random vectors.

Acceptance Criteria:
- `tests/test_ollama_service.py` validates embedding dimension consistency and cosine similarity calculations.
- Fallback mock works when the Ollama daemon is offline.

Prompt 4.2 — Persona Linkage & Entity Resolution Engine
Task: Build the entity resolution module linking disparate marketplace personas based on multi-factor stylometric and identifier overlap.

1. Create `ai/entity_resolution.py` with class `EntityResolver`:
   - Input: Candidate `ThreatActorProfile` and a list of existing profiles.
   - Calculate an Attribution Confidence Score (0.0 to 1.0) based on weighted factors:
     - Exact match on Hard Identifiers (Shared Wallet, Shared PGP, Shared IP): Confidence = 0.95 - 1.0.
     - Stylometric Vector Cosine Similarity >= 0.85: Weight = 0.50.
     - Classical Stylometry Similarity (TTR, Sentence Length, Punctuation frequency distance): Weight = 0.30.
     - Topic / Language similarity: Weight = 0.20.
   - Return linkage decision:
     - `matched`: bool (True if score >= configured threshold, e.g., 0.80)
     - `confidence_score`: float
     - `link_reasons`: list[str] (e.g., ["Exact Monero wallet match", "High stylometric cosine similarity (0.89)"])
     - `canonical_actor_id`: str (deterministic or existing cluster ID).

Acceptance Criteria:
- Unit tests confirm that `Persona A` and `Persona C` (from Loop 2.2) resolve to the same underlying threat actor cluster with confidence >= 0.80.


Loop 5: Neo4j Graph Modeling & Cypher Ingestion Engine
Prompt 5.1 — Neo4j Driver, Constraints & Schema Migrations
Task: Create the Neo4j database connection manager and schema initialization script.

1. Create `graph/driver.py`:
   - Thread-safe Neo4j driver singleton managing connection pools, retries, and clean teardown.
   - Verify connectivity on startup.

2. Create `graph/schema.py`:
   - Write migration functions executing Cypher constraints:
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (a:ThreatActor) REQUIRE a.actor_id IS UNIQUE;`
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (p:Persona) REQUIRE (p.handle, p.platform) IS NODE KEY;`
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (w:CryptoWallet) REQUIRE w.address IS UNIQUE;`
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (k:PGPKey) REQUIRE k.fingerprint IS UNIQUE;`
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (i:IPAddress) REQUIRE i.ip IS UNIQUE;`
     - `CREATE CONSTRAINT IF NOT EXISTS FOR (post:Post) REQUIRE post.post_id IS UNIQUE;`
     - Create vector index if supported, or B-tree indexes on `confidence` and `last_seen`.

Acceptance Criteria:
- `python -m graph.schema` executes successfully against a running Neo4j container without duplicate constraint errors.

Prompt 5.2 — Graph Ingestion Repository & Cypher Queries
Task: Implement idempotent Cypher query services to insert threat actor profiles, extracted identifiers, and linkage edges.

1. Create `graph/repository.py` with class `ThreatGraphRepository`:
   - Method `upsert_persona(profile: ThreatActorProfile, post: RawForumPost) -> None`:
     - Merge `(:Persona {handle: \(handle, platform:\)platform})`
     - Merge `(:Post {post_id: $post_id})`
     - Create `(:Persona)-[:AUTHORED]->(:Post)`
     - For each wallet in `profile.identifiers.crypto_wallets`:
       - Merge `(:CryptoWallet {address: \(address, currency:\)currency})`
       - Merge `(:Persona)-[:UTILIZES_WALLET {last_seen: $timestamp}]->(:CryptoWallet)`
     - For each PGP key:
       - Merge `(:PGPKey {fingerprint: $fingerprint})`
       - Merge `(:Persona)-[:OWNS_KEY]->(:PGPKey)`
     - For each IP address:
       - Merge `(:IPAddress {ip: $ip})`
       - Merge `(:Persona)-[:OBSERVED_IP]->(:IPAddress)`
     - Attach stylometric metadata properties to `Persona`.

   - Method `create_attribution_link(actor_id: str, persona_a_key: dict, persona_b_key: dict, confidence: float, reasons: list[str])`:
     - Merge `(:ThreatActor {actor_id: $actor_id})`
     - Link both Personas to the root `ThreatActor`:
       - Merge `(t:ThreatActor)-[:CONTROLS {confidence: $confidence}]->(p:Persona)`
     - Merge directional similarity edge between Personas:
       - Merge `(p1)-[r:LINKED_TO {confidence: \(confidence, reasons:\)reasons, method: 'stylometry_v1'}]->(p2)`

2. Implement a method `query_actor_network(actor_id: str) -> dict`:
   - Cypher query returning all linked handles, marketplaces, shared wallets, IPs, and average attribution confidence for export.

Acceptance Criteria:
- Integration tests in `tests/test_graph_repository.py` push synthetic personas and verify that the graph topology reflects all nodes and relationships idempotently.


Loop 6: Pipeline Integration, CLI & Export Engine
Prompt 6.1 — Core Processing Pipeline & CLI Runner
Task: Build the unified processing pipeline tying together NLP extraction, Ollama embeddings, entity resolution, and Neo4j graph storage.

1. Create `pipeline.py` with class `StylometryPipeline`:
   - Method `process_post(post: RawForumPost) -> ThreatActorProfile`:
     1. Extract classical stylometric features (`StylometryExtractor`).
     2. Extract crypto wallets, PGP, and IPs (`IdentifierExtractor`).
     3. Generate text embedding via Ollama (`OllamaStylometryService`).
     4. Query Neo4j for potential matches or candidate profiles.
     5. Execute `EntityResolver` to determine if this persona matches an existing threat actor cluster.
     6. Persist results into Neo4j using `ThreatGraphRepository`.
   - Method `process_batch(posts: list[RawForumPost])`:
     - Process a stream of raw posts with structured logging and progress tracking.

2. Create `main.py` CLI using `typer` or `argparse`:
   - Commands:
     - `init-db`: Run schema migrations and create constraints.
     - `ingest-fixtures`: Load `fixtures/sample_posts.json` and run the full pipeline.
     - `export-actor --actor-id  --format [csv|json]`: Export threat intelligence reports.
     - `run-worker`: Continuously poll or watch an input directory for new post files.

Acceptance Criteria:
- Running `python main.py ingest-fixtures` runs the entire synthetic dataset end-to-end without errors.
- Output logs clearly indicate extracted wallets and persona attribution matches.

Prompt 6.2 — Verification, Attribution Reporting & Export
Task: Implement export utilities to generate CSV, JSON, and threat intelligence summaries as required by NTRO specifications.

1. Create `export/reporter.py`:
   - Class `IntelligenceReporter`:
     - Method `export_json(actor_id: str, output_path: str)`:
       - Export deep actor profile: root actor ID, alias handles, platforms, all linked wallets, IPs, PGP fingerprints, confidence score, and timestamp timeline.
     - Method `export_csv(actor_id: str, output_path: str)`:
       - Flatten persona-to-identifier mappings for analyst spreadsheet ingestion.
     - Method `generate_summary_report(actor_id: str) -> str`:
       - Textual intelligence briefing: "Threat Actor [ID] operates across 2 marketplaces under handles 'X' and 'Y'. Linked via high stylometric similarity (0.87) and shared Monero wallet..."

2. Write full end-to-end integration test `tests/test_e2e_pipeline.py`:
   - Spin up/verify test containers.
   - Run pipeline against `sample_posts.json`.
   - Query Neo4j to confirm Persona C is successfully linked to Persona A.
   - Validate exported JSON contains all required indicators.

Acceptance Criteria:
- `pytest tests/test_e2e_pipeline.py` passes with 100% success.
- Output JSON file matches the expected NTRO intelligence deliverable format.