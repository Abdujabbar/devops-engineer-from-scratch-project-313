import pytest
from fastapi import status


def test_create_link(client, sample_link_data):
    """Test creating a new link."""
    response = client.post("/links", json=sample_link_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["original_url"] == sample_link_data["original_url"]
    assert data["short_name"] == sample_link_data["short_name"]
    assert (
        data["short_url"] == sample_link_data["short_name"]
    )  # short_url equals short_name when unique
    assert data["clicks"] == sample_link_data["clicks"]
    assert data["id"] is not None


def test_create_link_with_default_clicks(client):
    """Test creating a link without specifying clicks (should default to 0)."""
    link_data = {"original_url": "https://example.com", "short_name": "xyz789"}
    response = client.post("/links", json=link_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["clicks"] == 0
    assert data["short_url"] == "xyz789"


def test_create_link_validation_error(client):
    """Test creating a link with missing required fields."""
    invalid_data = {
        "original_url": "https://example.com"
        # missing short_name
    }
    response = client.post("/links", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_link(client, sample_link_data):
    """Test getting a specific link by ID."""
    # Create a link first
    create_response = client.post("/links", json=sample_link_data)
    created_link = create_response.json()
    link_id = created_link["id"]

    # Get the link
    response = client.get(f"/links/{link_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == sample_link_data["original_url"]
    assert data["short_name"] == sample_link_data["short_name"]
    assert data["short_url"] == sample_link_data["short_name"]
    assert data["clicks"] == sample_link_data["clicks"]


def test_get_link_not_found(client):
    """Test getting a non-existent link."""
    response = client.get("/links/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_list_links_empty(client):
    """Test listing links when there are no links."""
    response = client.get("/links")
    assert response.status_code == status.HTTP_416_RANGE_NOT_SATISFIABLE
    assert response.json() == []
    assert response.headers["Content-Range"] == "links */0"
    assert response.headers["Accept-Ranges"] == "links"


def test_list_links(client, sample_link_data):
    """Test listing all links."""
    # Create multiple links
    link1 = client.post("/links", json=sample_link_data).json()
    link2_data = {
        "original_url": "https://google.com",
        "short_name": "goog456",
        "clicks": 5,
    }
    link2 = client.post("/links", json=link2_data).json()

    # List all links (default range [0,10])
    response = client.get("/links")
    assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
    links = response.json()
    assert len(links) == 2

    # Verify headers (default range [0,10] but only 2 items exist)
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 0-1/2"
    assert "Accept-Ranges" in response.headers
    assert response.headers["Accept-Ranges"] == "links"

    # Verify both links are present
    link_ids = {link["id"] for link in links}
    assert link1["id"] in link_ids
    assert link2["id"] in link_ids


def test_list_links_pagination(client, sample_link_data):
    """Test listing links with range pagination."""
    # Create multiple links
    for i in range(5):
        link_data = {
            "original_url": f"https://example{i}.com",
            "short_name": f"link{i}",
            "clicks": i,
        }
        client.post("/links", json=link_data)

    # Test with range parameter
    response = client.get("/links?range=[2,3]")
    assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
    links = response.json()
    assert len(links) == 2
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "links 2-3/5"
    assert "Accept-Ranges" in response.headers
    assert response.headers["Accept-Ranges"] == "links"

    # Test range from beginning
    response = client.get("/links?range=[0,2]")
    assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
    links = response.json()
    assert len(links) == 3
    assert response.headers["Content-Range"] == "links 0-2/5"

    # Test range near end
    response = client.get("/links?range=[3,10]")
    assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
    links = response.json()
    assert len(links) == 2  # Only 2 items available (3-4)
    assert response.headers["Content-Range"] == "links 3-4/5"

    # Test without range (should use default [0,10])
    response = client.get("/links")
    assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
    links = response.json()
    assert len(links) == 5  # Default range [0,10] returns all 5 items
    assert response.headers["Content-Range"] == "links 0-4/5"


def test_update_link(client, sample_link_data):
    """Test updating a link."""
    # Create a link first
    create_response = client.post("/links", json=sample_link_data)
    link_id = create_response.json()["id"]

    # Update the link
    update_data = {
        "original_url": "https://updated.com",
        "short_name": "updated123",
        "clicks": 10,
    }
    response = client.put(f"/links/{link_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == update_data["original_url"]
    assert data["short_name"] == update_data["short_name"]
    assert data["short_url"] == update_data["short_name"]
    assert data["clicks"] == update_data["clicks"]


def test_update_link_partial(client, sample_link_data):
    """Test partial update of a link."""
    # Create a link first
    create_response = client.post("/links", json=sample_link_data)
    link_id = create_response.json()["id"]
    original_short_url = create_response.json()["short_url"]

    # Update only clicks
    update_data = {"clicks": 42}
    response = client.put(f"/links/{link_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["clicks"] == 42
    # Other fields should remain unchanged
    assert data["original_url"] == sample_link_data["original_url"]
    assert data["short_url"] == original_short_url


def test_update_link_not_found(client):
    """Test updating a non-existent link."""
    update_data = {"original_url": "https://updated.com", "short_name": "updated123"}
    response = client.put("/links/999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_link(client, sample_link_data):
    """Test deleting a link."""
    # Create a link first
    create_response = client.post("/links", json=sample_link_data)
    link_id = create_response.json()["id"]

    # Delete the link
    response = client.delete(f"/links/{link_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    get_response = client.get(f"/links/{link_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_link_not_found(client):
    """Test deleting a non-existent link."""
    response = client.delete("/links/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_and_list_links(client, sample_link_data):
    """Test that deleted links don't appear in the list."""
    # Create two links
    link1 = client.post("/links", json=sample_link_data).json()
    link2_data = {"original_url": "https://google.com", "short_name": "goog456"}
    link2 = client.post("/links", json=link2_data).json()

    # Verify both exist
    response = client.get("/links")
    assert len(response.json()) == 2

    # Delete one link
    client.delete(f"/links/{link1['id']}")

    # Verify only one remains
    response = client.get("/links")
    links = response.json()
    assert len(links) == 1
    assert links[0]["id"] == link2["id"]


def test_list_links_range_invalid_format(client):
    """Test list_links with invalid range format."""
    response = client.get("/links?range=invalid")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid range format" in response.json()["detail"]


def test_list_links_range_out_of_bounds(client, sample_link_data):
    """Test list_links with range beyond available items."""
    # Create one link
    client.post("/links", json=sample_link_data)

    # Request range beyond available items
    response = client.get("/links?range=[10,20]")
    assert response.status_code == status.HTTP_416_RANGE_NOT_SATISFIABLE
    assert response.headers["Content-Range"] == "links */1"
    assert response.json() == []


def test_list_links_range_invalid_start(client):
    """Test list_links with negative start value."""
    response = client.get("/links?range=[-1,10]")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Range start must be >= 0" in response.json()["detail"]


def test_list_links_range_end_before_start(client):
    """Test list_links with end before start."""
    response = client.get("/links?range=[10,5]")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Range end must be >= start" in response.json()["detail"]


def test_update_link_clicks_increment(client, sample_link_data):
    """Test updating only the clicks field."""
    # Create a link
    create_response = client.post("/links", json=sample_link_data)
    link_id = create_response.json()["id"]

    # Update clicks multiple times
    for new_clicks in [1, 5, 10]:
        update_data = {"clicks": new_clicks}
        response = client.put(f"/links/{link_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["clicks"] == new_clicks


def test_create_link_unique_short_url(client):
    """Test that duplicate short_name generates unique short_url with suffix."""
    # Create first link
    link1_data = {"original_url": "https://example.com", "short_name": "mylink"}
    link1 = client.post("/links", json=link1_data).json()
    assert link1["short_url"] == "mylink"

    # Create second link with same short_name
    link2_data = {"original_url": "https://example2.com", "short_name": "mylink"}
    link2 = client.post("/links", json=link2_data).json()
    assert link2["short_url"] == "mylink-1"
    assert link2["short_name"] == "mylink"

    # Create third link with same short_name
    link3_data = {"original_url": "https://example3.com", "short_name": "mylink"}
    link3 = client.post("/links", json=link3_data).json()
    assert link3["short_url"] == "mylink-2"
    assert link3["short_name"] == "mylink"


def test_update_link_short_name_regenerates_short_url(client):
    """Test that updating short_name regenerates short_url."""
    # Create a link
    link_data = {"original_url": "https://example.com", "short_name": "original"}
    link = client.post("/links", json=link_data).json()
    assert link["short_url"] == "original"

    # Update short_name
    update_data = {"short_name": "updated"}
    updated_link = client.put(f"/links/{link['id']}", json=update_data).json()
    assert updated_link["short_name"] == "updated"
    assert updated_link["short_url"] == "updated"
    assert updated_link["id"] == link["id"]


def test_update_link_short_name_with_existing_conflict(client):
    """Test updating short_name when the generated short_url already exists."""
    # Create two links
    link1_data = {"original_url": "https://example1.com", "short_name": "link1"}
    client.post("/links", json=link1_data).json()

    link2_data = {"original_url": "https://example2.com", "short_name": "link2"}
    link2 = client.post("/links", json=link2_data).json()

    # Update link2's short_name to match link1's short_name
    # Should generate unique short_url
    update_data = {"short_name": "link1"}
    updated_link2 = client.put(f"/links/{link2['id']}", json=update_data).json()
    assert updated_link2["short_name"] == "link1"
    assert (
        updated_link2["short_url"] == "link1-1"
    )  # Suffix added because link1 already uses "link1"
