# ThirdEye — Forensic Dark Web Intelligence Platform (Monorepo)

[![CI](https://github.com/manth07/Dark-Web_Deanonymization/actions/workflows/ai-graph.yml/badge.svg)](https://github.com/manth07/Dark-Web_Deanonymization/actions/workflows/ai-graph.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j 5.20](https://img.shields.io/badge/neo4j-5.20--community-green.svg)](https://neo4j.com/)
[![Tests](https://img.shields.io/badge/tests-51%20passed-brightgreen.svg)](ai-graph/tests/)
[![License](https://img.shields.io/badge/license-Proprietary%20%2F%20NTRO-red.svg)]()

**Smart India Hackathon (SIH ID: 26151)**  
**Organization:** National Technical Research Organisation (NTRO)  
**Theme:** Blockchain & Cybersecurity  

---

## 🏗️ Repository Architecture

This repository consolidates the entire forensic intelligence ecosystem into 4 modular, isolated service folders for conflict-free multi-team collaboration:

```text
.
├── frontend/          # Next.js & React Flow UI Dashboard
├── backend/           # Production-ready FastAPI Core Engine, SQLModel & Alembic
├── scraper/           # Tor & Dark Web Crawler / Intelligence Scraping Service
├── ai-graph/          # AI Relationship Network & Link Analysis Engine (My Role)
│   ├── core/          # Configuration & structured logging
│   ├── schemas/       # Pydantic v2 contract models
│   ├── nlp/           # Classical stylometry & technical identifier harvester
│   ├── ai/            # Local Ollama embeddings & entity resolution engine
│   ├── graph/         # Neo4j driver, idempotent schema migrations & repository
│   ├── fixtures/      # Synthetic dark web corpus & generator
│   ├── tests/         # Comprehensive pytest verification suite (51/51 passed)
│   ├── pipeline.py    # Unified processing pipeline (StylometryPipeline)
│   ├── main.py        # Typer / Rich Command Line Interface
│   ├── requirements.txt # Pinned production dependencies
│   └── Dockerfile     # Container definition with pre-cached NLP models
├── Brain/             # Architecture specifications, contracts, and prompt history
├── docker-compose.yml # Orchestrates Neo4j, Ollama, and ai-graph engine
├── prompts.md         # Loop engineering prompts
├── .gitignore         # Monorepo gitignore rules
└── README.md          # Project overview and documentation
```

---

## 🧩 Sub-System Overview

| Module | Role | Technology Stack | Status |
|---|---|---|:---:|
| [`frontend/`](frontend/) | Interactive analyst GUI, React Flow relationship graph canvas, timeline filters | Next.js, React Flow, Tailwind CSS, TypeScript | Scaffolded |
| [`backend/`](backend/) | Core API gateway, SQLModel relational metadata, Alembic migrations, NTRO exports | FastAPI, SQLModel, Alembic, PostgreSQL, Neo4j Driver | Active |
| [`scraper/`](scraper/) | Autonomous Tor crawler, `.onion` scraping, infrastructure TLS/header fingerprinting | Python 3.11, Tor SOCKS5 Proxy, Playwright, Scrapy | Scaffolded |
| [`ai-graph/`](ai-graph/) | Classical stylometry, multi-currency crypto extraction, Ollama embeddings, Neo4j resolution | Python 3.11, spaCy, NLTK, Neo4j, Ollama, Scikit-learn, Typer | **100% Complete (51/51 Tests Passed)** |

---

## ⚡ Quickstart & Docker Orchestration

The root `docker-compose.yml` orchestrates the local intelligence stack (`neo4j:5.20-community`, `ollama/ollama:latest`, and `ai-graph`):

```powershell
# Validate docker-compose configuration
docker compose config

# Spin up Neo4j and Ollama services
docker compose up -d neo4j ollama

# Build and run the ai-graph service
docker compose up --build ai-graph
```

---

## 🔬 AI-Graph Subsystem Capabilities

The `ai-graph/` engine operates autonomously to de-anonymize migrated or rebranded threat actors:

1. **Multi-Currency Forensic Harvester**: Validates BTC (P2PKH, P2SH, Bech32), XMR (standard, integrated), ETH (`0x...`), PGP keys/fingerprints, and RFC 1918 filtered IPv4 indicators.
2. **Classical Forensic Stylometry**: Extracts lexical metrics (TTR, sentence lengths, Hapax Legomena), syntactic cadence (POS tags, function words), and structural signatures.
3. **Privacy-Preserving Embeddings**: Strips overt identifiers before computing 768-dim dense semantic embeddings via local Ollama models (`qwen2.5` / `nomic-embed-text`) with deterministic offline mock vector fallback.
4. **Graph-Based Entity Resolution**: Computes explainable attribution confidence scores combining hard cryptographic identifiers, dense vector cosine similarity, and stylometric cadence.
5. **Idempotent Neo4j Persistence**: Enforces 6 constraints and 3 B-tree indexes to maintain clean, duplicate-free identity graphs.
6. **NTRO Intelligence Packages**: Generates law-enforcement-compliant JSON deliverables, analyst CSV spreadsheets, and textual executive briefings.

### Running AI-Graph CLI & Tests Locally

```powershell
# Navigate into ai-graph module
cd ai-graph

# Run the 51-test suite
pytest -v

# Run the end-to-end ingestion pipeline
python main.py ingest-fixtures

# Export NTRO deliverables for attributed actor
python main.py export-actor --actor-id actor-92a41cc0 --format both
```

---

## 🚀 Environment Setup & Guidelines

Each service maintains its local environment configuration. For root:
```powershell
copy .env.example .env
```

### Git Branching Strategy
- `main`: Production release branch.
- `dev/<subsystem>`: Per-folder integration branch (e.g., `dev/ai-graph`, `dev/backend`).
- `feature/<subsystem>-<feature-name>`: Feature development branches.

---

## 🛡️ License & Classification
Confidential Forensic Dark Web Intelligence System — SIH Edition // NTRO Spec.
