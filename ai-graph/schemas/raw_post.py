"""Raw dark web forum post schema."""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RawForumPost(BaseModel):
    """Represents a raw post or listing captured from a dark web forum or marketplace."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    post_id: str = Field(..., description="Unique post identifier or UUID", validation_alias="record_id")
    forum_name: str = Field(..., description="Forum or marketplace name", validation_alias="marketplace")
    author_handle: str = Field(..., description="Author username or vendor handle", validation_alias="actor_handle")
    raw_content: str = Field(..., description="Unprocessed raw message text", validation_alias="raw_text")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Publication timestamp (ISO-8601)",
    )
    thread_title: Optional[str] = Field(default=None, description="Thread or discussion topic title")
    source_url: Optional[str] = Field(default=None, description="Source onion URL or anonymized source reference")
    reliability_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Source reliability rating")

    @field_validator("raw_content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure post content is a string."""
        if not isinstance(v, str):
            raise ValueError("raw_content must be a string")
        return v
