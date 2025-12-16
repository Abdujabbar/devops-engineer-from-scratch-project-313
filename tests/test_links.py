import pytest
from fastapi import status


def test_create_link(client, sample_link_data):
    """Test creating a new link."""
    response = client.post("/api/links", json=sample_link_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["original_url"] == sample_link_data["original_url"]
    assert data["short_name"] == sample_link_data["short_name"]
    assert data["short_url"] == sample_link_data["short_name"]  # short_url is generated from short_name
    assert data["id"] is not None


def test_create_link_with_default_clicks(client):
    """Test creating a link with short_name."""
    link_data = {
        "original_url": "https://example.com",
        "short_name": "xyz789"
    }
    response = client.post("/api/links", json=link_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["short_name"] == "xyz789"
    assert data["short_url"] == "xyz789"  # short_url is generated from short_name


def test_create_link_validation_error(client):
    """Test creating a link with missing required fields."""
    invalid_data = {
        "original_url": "https://example.com"
        # missing short_name
    }
    response = client.post("/api/links", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_link(client, sample_link_data):
    """Test getting a specific link by ID."""
    # Create a link first
    create_response = client.post("/api/links", json=sample_link_data)
    created_link = create_response.json()
    link_id = created_link["id"]
    
    # Get the link
    response = client.get(f"/api/links/{link_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == sample_link_data["original_url"]
    assert data["short_name"] == sample_link_data["short_name"]
    assert data["short_url"] == sample_link_data["short_name"]  # short_url is generated from short_name


def test_get_link_not_found(client):
    """Test getting a non-existent link."""
    response = client.get("/api/links/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_list_links_empty(client):
    """Test listing links when there are no links."""
    response = client.get("/api/links")
    # When there are no links, the API returns 416 (Range Not Satisfiable) with empty list
    assert response.status_code == status.HTTP_416_RANGE_NOT_SATISFIABLE
    assert response.json() == []


def test_list_links(client, sample_link_data):
    """Test listing all links."""
    # Create multiple links
    link1 = client.post("/api/links", json=sample_link_data).json()
    link2_data = {
        "original_url": "https://google.com",
        "short_name": "goog456",
    }
    link2 = client.post("/api/links", json=link2_data).json()
    
    # List all links
    response = client.get("/api/links")
    assert response.status_code == status.HTTP_200_OK
    links = response.json()
    assert len(links) == 2
    
    # Verify both links are present
    link_ids = {link["id"] for link in links}
    assert link1["id"] in link_ids
    assert link2["id"] in link_ids


def test_list_links_pagination(client, sample_link_data):
    """Test listing links with pagination using range parameter."""
    # Create multiple links
    for i in range(5):
        link_data = {
            "original_url": f"https://example{i}.com",
            "short_name": f"link{i}",
        }
        client.post("/api/links", json=link_data)
    
    # Test with range parameter [start, end]
    response = client.get("/api/links?range=[2,3]")
    assert response.status_code == status.HTTP_200_OK
    links = response.json()
    assert len(links) == 2
    
    # Test range for first 3 items
    response = client.get("/api/links?range=[0,2]")
    assert response.status_code == status.HTTP_200_OK
    links = response.json()
    assert len(links) == 3
    
    # Test range for last item
    response = client.get("/api/links?range=[4,4]")
    assert response.status_code == status.HTTP_200_OK
    links = response.json()
    assert len(links) == 1


def test_update_link(client, sample_link_data):
    """Test updating a link."""
    # Create a link first
    create_response = client.post("/api/links", json=sample_link_data)
    link_id = create_response.json()["id"]
    
    # Update the link
    update_data = {
        "original_url": "https://updated.com",
        "short_name": "updated123",
    }
    response = client.put(f"/api/links/{link_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == link_id
    assert data["original_url"] == update_data["original_url"]
    assert data["short_name"] == update_data["short_name"]
    assert data["short_url"] == update_data["short_name"]  # short_url is regenerated from short_name


def test_update_link_not_found(client):
    """Test updating a non-existent link."""
    update_data = {
        "original_url": "https://updated.com",
        "short_name": "updated123"
    }
    response = client.put("/api/links/999", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_link(client, sample_link_data):
    """Test deleting a link."""
    # Create a link first
    create_response = client.post("/api/links", json=sample_link_data)
    link_id = create_response.json()["id"]
    
    # Delete the link
    response = client.delete(f"/api/links/{link_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify it's deleted
    get_response = client.get(f"/api/links/{link_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_link_not_found(client):
    """Test deleting a non-existent link."""
    response = client.delete("/api/links/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_and_list_links(client, sample_link_data):
    """Test that deleted links don't appear in the list."""
    # Create two links
    link1 = client.post("/api/links", json=sample_link_data).json()
    link2_data = {
        "original_url": "https://google.com",
        "short_name": "goog456"
    }
    link2 = client.post("/api/links", json=link2_data).json()
    
    # Verify both exist
    response = client.get("/api/links")
    assert len(response.json()) == 2
    
    # Delete one link
    client.delete(f"/api/links/{link1['id']}")
    
    # Verify only one remains
    response = client.get("/api/links")
    links = response.json()
    assert len(links) == 1
    assert links[0]["id"] == link2["id"]


