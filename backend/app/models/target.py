import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ThreatActor(SQLModel, table=True):
    """Forensic dark web threat actor entity table."""

    __tablename__ = "threat_actors"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        description="Unique UUID identifier for threat actor",
    )
    handle: str = Field(
        index=True,
        nullable=False,
        description="Dark web alias, handle, or username",
    )
    risk_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Threat risk score rating between 0 and 100",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the threat actor is currently active",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="UTC timestamp when target was recorded",
    )


class InfrastructureNode(SQLModel, table=True):
    """Infrastructure host/server node table."""

    __tablename__ = "infrastructure_nodes"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        description="Unique UUID identifier for infrastructure node",
    )
    ip_address: str = Field(
        index=True,
        nullable=False,
        description="IP address or host entry",
    )
    server_banner: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Captured server header banner or signature",
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="UTC timestamp when node was discovered",
    )
