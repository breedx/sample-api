"""
Shared pytest fixtures and configuration

TODO: Implement fixtures for:
- Base test client
- Authenticated clients per tenant
- Test data factories
- Database cleanup
- Environment configuration
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app, tenants_db, users_db, files_db, file_storage, blacklisted_tokens


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Automatically reset all databases before each test"""
    tenants_db.clear()
    users_db.clear()
    files_db.clear()
    file_storage.clear()
    blacklisted_tokens.clear()
    yield  # Test runs here
    # Cleanup after test
    tenants_db.clear()
    users_db.clear()
    files_db.clear()
    file_storage.clear()
    blacklisted_tokens.clear()


# TODO: Add fixtures for authenticated clients
# Example:
# @pytest.fixture
# def tenant_a_admin(client):
#     """Return authenticated admin client for Tenant A"""
#     # Register tenant
#     client.post("/auth/register", json={...})
#     # Login and get token
#     response = client.post("/auth/login", json={...})
#     token = response.json()["access_token"]
#     # Set authorization header
#     client.headers = {"Authorization": f"Bearer {token}"}
#     return client
