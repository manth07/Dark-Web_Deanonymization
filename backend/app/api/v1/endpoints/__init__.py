"""Endpoints package for API v1."""

from app.api.v1.endpoints.dossier import router as dossier_router
from app.api.v1.endpoints.graph import router as graph_router
from app.api.v1.endpoints.health import router as health_router

__all__ = ["health_router", "graph_router", "dossier_router"]
