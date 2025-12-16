import re
from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional

from shortener.db import get_session
from shortener.models.link import Link
from shortener.schemas.link import LinkCreate, LinkUpdate


router = APIRouter(prefix="/links", tags=["Links"])


def generate_unique_short_url(
    short_name: str, session: Session, exclude_link_id: Optional[int] = None
) -> str:
    """
    Generate a unique short_url based on short_name.
    If short_url already exists, append a numeric suffix.

    Args:
        short_name: The base name for the short URL
        session: Database session
        exclude_link_id: Optional link ID to exclude from uniqueness check (for updates)
    """
    base_short_url = short_name
    short_url = base_short_url
    counter = 1

    # Check if short_url exists and generate unique one
    while True:
        statement = select(Link).where(Link.short_url == short_url)
        if exclude_link_id is not None:
            statement = statement.where(Link.id != exclude_link_id)

        existing = session.exec(statement).first()

        if not existing:
            break

        # Generate new short_url with suffix
        short_url = f"{base_short_url}-{counter}"
        counter += 1

    return short_url


@router.post("", response_model=Link, status_code=status.HTTP_201_CREATED)
def create_link(link_data: LinkCreate, session: Session = Depends(get_session)):
    """Create a new link with auto-generated unique short_url."""
    # Generate unique short_url from short_name
    short_url = generate_unique_short_url(link_data.short_name, session)

    # Create link with generated short_url
    link = Link(
        original_url=link_data.original_url,
        short_name=link_data.short_name,
        short_url=short_url,
        # clicks=link_data.clicks,
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@router.get("", response_model=List[Link])
def list_links(
    response: Response,
    session: Session = Depends(get_session),
    range: str = Query("[0,10]", description="Range in format [start,end]"),
):
    """
    Get all links with range-based pagination.
    Supports range query parameter: ?range=[0,10]
    Default range: [0,10]
    Returns Content-Range header: links 0-10/42
    """
    # Get total count of links
    count_statement = select(func.count(Link.id))
    total_count = session.exec(count_statement).one()

    # Set Accept-Ranges header to indicate supported range unit
    response.headers["Accept-Ranges"] = "links"

    # Parse range parameter (now always provided with default [0,10])
    range_match = re.match(r"\[(-?\d+)\s*,\s*(-?\d+)\]", range)
    if not range_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid range format. Expected format: [start,end]",
        )

    start = int(range_match.group(1))
    end = int(range_match.group(2))

    # Validate range
    if start < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Range start must be >= 0"
        )

    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Range end must be >= start"
        )

    # Handle unsatisfiable range (start >= total_count)
    if total_count == 0:
        # No items exist
        response.headers["Content-Range"] = "links */0"
        response.status_code = status.HTTP_416_RANGE_NOT_SATISFIABLE
        return []

    if start >= total_count:
        # Range starts beyond available items
        response.headers["Content-Range"] = f"links */{total_count}"
        response.status_code = status.HTTP_416_RANGE_NOT_SATISFIABLE
        return []

    # Ensure end doesn't exceed total_count - 1
    if end >= total_count:
        end = total_count - 1

    # Calculate limit and offset
    limit = end - start + 1
    offset = start

    # Query links with range
    statement = select(Link).offset(offset).limit(limit).order_by(Link.id)
    links = session.exec(statement).all()

    # Build Content-Range header: links start-end/total
    content_range = f"links {start}-{end}/{total_count}"
    response.headers["Content-Range"] = content_range

    return links


@router.get("/{link_id}", response_model=Link)
def get_link(link_id: int, session: Session = Depends(get_session)):
    """Get a specific link by ID."""
    link = session.get(Link, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link with id {link_id} not found",
        )
    return link


@router.put("/{link_id}", response_model=Link)
def update_link(
    link_id: int, link_update: LinkUpdate, session: Session = Depends(get_session)
):
    """Update a link by ID."""
    link = session.get(Link, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link with id {link_id} not found",
        )

    link_data = link_update.model_dump(exclude_unset=True)

    # If short_name is being updated, regenerate short_url
    if "short_name" in link_data:
        new_short_name = link_data["short_name"]
        # Generate unique short_url from new short_name, excluding current link
        new_short_url = generate_unique_short_url(
            new_short_name, session, exclude_link_id=link_id
        )
        link.short_name = new_short_name
        link.short_url = new_short_url
        # Remove short_name from link_data to avoid setting it again
        del link_data["short_name"]

    # Update other fields
    for field, value in link_data.items():
        setattr(link, field, value)

    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(link_id: int, session: Session = Depends(get_session)):
    """Delete a link by ID."""
    link = session.get(Link, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link with id {link_id} not found",
        )

    session.delete(link)
    session.commit()
    return None
