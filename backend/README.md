# ThirdEye - Forensic Dark Web Intelligence Platform (Backend Core)

Production-ready, highly modular **FastAPI** backend architecture tailored for **ThirdEye**, an AI-driven forensic dark web intelligence and threat analysis platform built for security analysts, forensic investigators, and law enforcement.

---

## 📁 Architecture & Project Structure

```
thirdeye-backend/
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

## ⚡ Core Features

- **Pydantic v2 & Pydantic Settings**: Strongly-typed settings class parsing string arrays and JSON lists from `.env`.
- **System Diagnostics & Health API**: Endpoint `/api/v1/health` providing platform operational status, version `2.0-SIH`, precise server UTC timestamp, system RAM usage, and process RSS/VMS memory statistics.
- **Security & Headers**: Built-in HTTP security header enforcement middleware (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`, `HSTS`) and token authentication stubs.
- **Modern Next.js CORS Integration**: Fully configured CORS middleware supporting development (`localhost:3000`, `127.0.0.1:3000`) and configurable production origins.
- **Lifespan Context Management**: Clean startup and shutdown event handling using FastAPI `asynccontextmanager`.
- **Forensic Data Models & Services**: SQLModel schemas and business services for target tracking, intelligence dossiers, and graph link analysis.

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

### Sample `/api/v1/health` Response
```json
{
  "status": "operational",
  "version": "2.0-SIH",
  "timestamp": "2026-09-21T22:15:00.000Z",
  "uptime_seconds": 12.45,
  "environment": "development",
  "memory": {
    "total_mb": 16384.0,
    "available_mb": 10240.5,
    "used_mb": 6143.5,
    "percent_used": 37.5,
    "process_rss_mb": 45.2,
    "process_vms_mb": 210.8
  },
  "dependencies": {
    "database": "postgresql+asyncpg (configured)",
    "threat_crawler": "active",
    "graph_engine": "operational"
  }
}
```

---

## 🛡️ License & Classification
Confidential Forensic Dark Web Intelligence System — SIH Edition.
