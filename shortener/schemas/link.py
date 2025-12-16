from typing import Optional
from pydantic import BaseModel


class LinkCreate(BaseModel):
    """Schema for creating a link."""

    original_url: str
    short_name: str
    clicks: int = 0


class LinkUpdate(BaseModel):
    """Schema for updating a link."""

    original_url: Optional[str] = None
    short_name: Optional[str] = None
    clicks: Optional[int] = None

