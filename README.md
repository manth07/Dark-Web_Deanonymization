# ThirdEye - Forensic Dark Web Intelligence Platform (Monorepo)

Welcome to the **ThirdEye** monorepo repository (`thirdeye-darkweb-intel`). This repository consolidates the entire forensic intelligence ecosystem into 4 modular, isolated service folders for multi-team collaboration without Git merge conflicts.

---

## 📁 Repository Structure

```
thirdeye-darkweb-intel/
├── frontend/             # Next.js & React Flow UI Dashboard
├── backend/              # Production-ready FastAPI Core Engine, SQLModel & Alembic
├── scraper/              # Tor & Dark Web Crawler / Intelligence Scraping Service
└── ai-graph/             # AI Relationship Network & Link Analysis Engine
```

---

## 🧩 Sub-System Overview

### 1. `backend/` — Core Intelligence Engine
- **Framework**: FastAPI (Python 3.10+) with async architecture.
- **Database**: PostgreSQL (Neon Serverless) with SQLModel ORM and AsyncEngine.
- **Migrations**: Alembic with async migration support (`alembic upgrade head`).
- **PDF Evidence Export**: ReportLab PDF dossier compiler (`POST /api/v1/dossier/generate`).
- **Graph Endpoints**: React Flow graph mock data provider (`GET /api/v1/graph/mock/{target_handle}`).
- **Setup & Execution**:
  ```bash
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```

### 2. `frontend/` — UI Dashboard
- React / Next.js dashboard featuring React Flow node visualization, risk metrics, and PDF dossier download buttons.

### 3. `scraper/` — Dark Web Intelligence Scraper
- Tor onion network crawler, forum monitoring, and market scraping pipelines.

### 4. `ai-graph/` — AI Relationship Graph Analytics
- Graph neural network models and correlation engines for entity link analysis.

---

## 🚀 Quick Setup & Workflow Guidelines

### Environment Setup (`.env`)
Each service maintains its isolated local environment configuration. For `backend/`, copy or configure `.env`:
```env
PROJECT_NAME="ThirdEye - Threat Intel Core"
API_V1_STR="/api/v1"
DEBUG=True
DATABASE_URL="postgresql+asyncpg://<USER>:<PASS>@<HOST>/<DB>?sslmode=require"
ALLOWED_ORIGINS='["http://localhost:3000", "http://127.0.0.1:3000"]'
```

### Git Branching Strategy
- `main`: Production release branch.
- `feature/<subsystem>-<feature-name>`: Feature development branches (e.g., `feature/frontend-react-flow`, `feature/backend-auth`).

---

## 🛡️ License & Classification
Confidential Forensic Dark Web Intelligence System — SIH Edition.
