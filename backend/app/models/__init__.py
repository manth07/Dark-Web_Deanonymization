"""SQLModel / SQLAlchemy database models for ThirdEye backend."""

from app.models.target import InfrastructureNode, ThreatActor

# Import all models here so SQLModel.metadata registers every table schema for Alembic migrations.
__all__ = [
    "ThreatActor",
    "InfrastructureNode",
]
