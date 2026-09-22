"""Pydantic v2 Schemas for API requests, responses, and internal DTOs."""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.dossier import DossierRequestSchema
from app.schemas.graph import EdgeSchema, GraphResponseSchema, NodeSchema

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API envelope model."""

    success: bool = Field(default=True, description="Indicates if the request succeeded")
    data: Optional[T] = Field(default=None, description="Response payload")
    error: Optional[str] = Field(default=None, description="Error details if unsuccessful")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="UTC response timestamp"
    )


class MemoryMetrics(BaseModel):
    """Memory usage statistics schema."""

    total_mb: float = Field(..., description="Total system memory in Megabytes")
    available_mb: float = Field(..., description="Available system memory in Megabytes")
    used_mb: float = Field(..., description="Used system memory in Megabytes")
    percent_used: float = Field(..., description="Percentage of system RAM utilized")
    process_rss_mb: float = Field(..., description="Process Resident Set Size in MB")
    process_vms_mb: float = Field(..., description="Process Virtual Memory Size in MB")


class SystemHealthResponse(BaseModel):
    """Detailed health check status response model."""

    status: str = Field(..., example="operational", description="Current backend status")
    version: str = Field(..., example="2.0-SIH", description="Platform release version")
    timestamp: datetime = Field(..., description="Current server UTC timestamp")
    uptime_seconds: float = Field(..., description="Seconds since service startup")
    environment: str = Field(..., example="production", description="Environment mode")
    memory: MemoryMetrics = Field(..., description="System and process memory statistics")
    dependencies: dict[str, str] = Field(
        default_factory=dict, description="Status of connected services (Database, Redis, etc.)"
    )


class DossierCreateSchema(BaseModel):
    """Schema for requesting dark web entity dossier generation."""

    target_identifier: str = Field(
        ..., example="shadow_broker_99.onion", description="Dark web handle, alias, or onion URL"
    )
    threat_level: str = Field(
        default="HIGH", example="CRITICAL", description="Assessed initial threat severity level"
    )
    include_graph: bool = Field(
        default=True, description="Whether to compute entity relationship network graph"
    )
    tags: list[str] = Field(
        default_factory=list, example=["ransomware", "tor_forum"], description="Metadata tags"
    )


class IntelligenceNodeSchema(BaseModel):
    """Schema representing an entity node in the intelligence graph."""

    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label or entity alias")
    node_type: str = Field(
        ..., example="CRYPTO_WALLET", description="Type of node (FORUM, WALLET, PGP_KEY, IP)"
    )
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score between 0 and 100")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary forensic attributes"
    )

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "APIResponse",
    "MemoryMetrics",
    "SystemHealthResponse",
    "DossierCreateSchema",
    "DossierRequestSchema",
    "IntelligenceNodeSchema",
    "NodeSchema",
    "EdgeSchema",
    "GraphResponseSchema",
]
