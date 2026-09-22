"""Pydantic v2 schema definitions for forensic dossier generation requests."""

from pydantic import BaseModel, Field


class DossierRequestSchema(BaseModel):
    """Schema for requesting PDF evidence dossier generation."""

    target_handle: str = Field(
        ...,
        json_schema_extra={"example": "shadow_broker_99"},
        description="Target threat actor handle, username, or dark web alias",
    )
    findings: list[str] = Field(
        ...,
        json_schema_extra={
            "example": [
                "Identified primary Bitcoin wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa with 154.2 BTC total volume.",
                "Associated with dark web Dread forum alias 'shadow_op'.",
                "Infrastructure traced to Tor exit node IP 198.51.100.42 hosted in Germany.",
            ]
        },
        description="List of forensic intelligence findings to include in the generated dossier report",
    )
