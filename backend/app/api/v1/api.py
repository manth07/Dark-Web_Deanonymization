"""API v1 master router aggregating all endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import dossier, graph, health

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["Health & Status Check"])
api_router.include_router(graph.router, prefix="/graph", tags=["Intelligence Graph"])
api_router.include_router(dossier.router, prefix="/dossier", tags=["Evidence Export"])
