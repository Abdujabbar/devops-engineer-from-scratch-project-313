from typing import Optional
from pydantic import BaseModel, ConfigDict


class LinkCreate(BaseModel):
    """Schema for creating a link."""

    original_url: str
    short_name: str
    # clicks: int = 0


class LinkUpdate(BaseModel):
    """Schema for updating a link."""

    original_url: Optional[str] = None
    short_name: Optional[str] = None
    # clicks: Optional[int] = None


class LinkSchema(BaseModel):
    """Schema for link responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    short_name: str
    short_url: str
    # clicks: int = 0
