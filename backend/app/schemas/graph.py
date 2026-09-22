"""Pydantic v2 schemas defining intelligence graph network visualization structures."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class NodeSchema(BaseModel):
    """Schema representing an entity node in the React Flow graph."""

    id: str = Field(..., description="Unique node identifier string")
    label: str = Field(
        ..., example="Actor", description="Entity category label (e.g., Actor, Wallet, IP)"
    )
    name: str = Field(..., example="shadow_broker_99", description="Human-readable node display name")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Arbitrary key-value metadata attributes for rendering"
    )


class EdgeSchema(BaseModel):
    """Schema representing a relationship edge between two nodes."""

    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    relation_type: str = Field(
        ..., example="OWNS_WALLET", description="Relationship type description (e.g. OWNS_WALLET, HOSTED_ON)"
    )


class GraphResponseSchema(BaseModel):
    """Response payload containing full node and edge network graph structures."""

    nodes: list[NodeSchema] = Field(..., description="List of graph nodes")
    edges: list[EdgeSchema] = Field(..., description="List of connecting graph edges")
