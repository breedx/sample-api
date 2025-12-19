"""
Example pytest test file for User Management API

This file contains ONE example test to get you started.
Your task is to add comprehensive test coverage for all endpoints.

pytest basics:
- Test functions must start with 'test_'
- Use assert statements for validation
- Use fixtures for setup/teardown
- Run with: pytest -v
"""
import pytest
from fastapi.testclient import TestClient
from py.main import app, users_db


# Fixture example - this runs before each test
@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """Automatically reset database before each test"""
    users_db.clear()
    yield  # Test runs here
    users_db.clear()  # Cleanup after test


# Example test - THIS IS YOUR STARTING POINT
def test_health_check(client):
    """Test that the health check endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "timestamp" in response.json()


# TODO: Add more tests below
# Suggested tests to implement:
#
# 1. test_create_user_success - Create a valid user
# 2. test_create_user_duplicate_username - Try to create user with existing username
# 3. test_create_user_duplicate_email - Try to create user with existing email
# 4. test_create_user_invalid_email - Test email validation
# 5. test_create_user_invalid_username_too_short - Test username length validation
# 6. test_list_users_empty - List users when database is empty
# 7. test_list_users_with_data - List users with multiple users
# 8. test_list_users_active_only - Test the active_only filter
# 9. test_get_user_success - Get a specific user by ID
# 10. test_get_user_not_found - Try to get non-existent user
# 11. test_update_user_success - Update user information
# 12. test_update_user_not_found - Try to update non-existent user
# 13. test_update_user_email_conflict - Try to update to existing email
# 14. test_delete_user_soft_delete - Test soft delete (is_active=False)
# 15. test_delete_user_permanent - Test permanent deletion
# 16. test_delete_user_not_found - Try to delete non-existent user
#
# BONUS challenges:
# - Use pytest.mark.parametrize for testing multiple inputs
# - Create custom fixtures for common test data
# - Test error messages match expected format
# - Test timestamp updates on user modifications
