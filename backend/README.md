# ThirdEye - Forensic Dark Web Intelligence Platform (Backend Core)

Production-ready, highly modular **FastAPI** backend architecture tailored for **ThirdEye**, an AI-driven forensic dark web intelligence and threat analysis platform built for security analysts, forensic investigators, and law enforcement.

**Technology Stack:** FastAPI, SQLModel, Alembic, PostgreSQL, Neo4j Python Driver, Pydantic v2

---

## 📁 Architecture & Project Structure

```
backend/
├── app/
│   ├── __init__.py             # Core package initialization (v2.0-SIH)
│   ├── main.py                 # FastAPI application setup, CORS, lifespan events & routing
│   ├── core/
│   │   ├── __init__.py         # Core exports
│   │   ├── config.py           # Pydantic Settings BaseSettings loading from .env
│   │   └── security.py         # Security headers middleware & bearer token stubs
│   ├── api/
│   │   ├── __init__.py         # API package initialization
│   │   └── v1/
│   │       ├── __init__.py     # API v1 package exports
│   │       ├── api.py          # Master APIRouter aggregating sub-routers
│   │       └── endpoints/
│   │           ├── __init__.py # Endpoints export package
│   │           └── health.py   # Health diagnostics, RAM/process memory metrics
│   ├── models/                 # SQLModel / SQLAlchemy database models
│   │   └── __init__.py         # Target, Dossier, and IntelligenceNode models
│   ├── schemas/                # Pydantic v2 DTOs and API validation schemas
│   │   └── __init__.py         # Health, Dossier, and Network Graph schemas
│   └── services/               # Core business logic layer
│       └── __init__.py         # Dossier generation & relationship graph service engine
├── .env                        # Environment variable configuration
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Production dependencies
└── README.md                   # Architectural documentation
```

---

## ⚡ Core Features & Responsibilities

- **FastAPI REST API**:
  - `GET /api/v1/health`: Health status, version `2.0-SIH`, UTC timestamp & memory metrics.
  - `GET /api/v1/actors`: Paginated, timeline-filtered, and confidence-filtered list of threat actors.
  - `GET /api/v1/actors/{actor_id}`: Full actor profile with alias handles, crypto wallets, and attribution scores.
  - `GET /api/v1/actors/{actor_id}/graph`: Node-and-link JSON schema for React Flow canvas visualization.
  - `GET /api/v1/export`: Asynchronous generation of NTRO-compliant JSON, CSV, and summary reports.
- **Relational Metadata Store**:
  - SQLModel & PostgreSQL for analyst session logs, audit trails, source configurations, and query caching.
  - Alembic for deterministic database schema migrations.
- **Neo4j Read Gateway**:
  - Executes parameterized Cypher read queries against the identity graph maintained by `ai-graph`.
- **Security & Headers**: Built-in HTTP security header enforcement middleware (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`, `HSTS`) and token authentication stubs.
- **Modern Next.js CORS Integration**: Fully configured CORS middleware supporting development (`localhost:3000`, `127.0.0.1:3000`) and configurable production origins.
- **Lifespan Context Management**: Clean startup and shutdown event handling using FastAPI `asynccontextmanager`.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Environment Setup
Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration (`.env`)
Verify `.env` configuration file exists at the root:
```env
PROJECT_NAME="ThirdEye - Threat Intel Core"
API_V1_STR="/api/v1"
DEBUG=True
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/thirdeye"
ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

### 5. Running the Application
Launch the server using Uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: `http://localhost:8000`

---

## 📖 API Documentation & Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Service overview & documentation links |
| `/docs` | `GET` | Interactive Swagger UI documentation |
| `/redoc` | `GET` | ReDoc API documentation |
| `/api/v1/health` | `GET` | Health status, version `2.0-SIH`, UTC timestamp & memory metrics |
| `/api/v1/actors` | `GET` | Filtered list of threat actors |
| `/api/v1/actors/{id}` | `GET` | Target actor profile and identifiers |
| `/api/v1/actors/{id}/graph` | `GET` | Graph relationship visualization data |
| `/api/v1/export` | `GET` | NTRO deliverable export |

---

## 🛡️ License & Classification
Confidential Forensic Dark Web Intelligence System — SIH Edition.
