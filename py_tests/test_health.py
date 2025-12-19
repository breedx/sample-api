"""
Basic health check test - Example to get you started
"""
import pytest


@pytest.mark.smoke
def test_health_check(client):
    """Test that the health check endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data
