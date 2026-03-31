"""
Tests for user management endpoints.
"""
import pytest
from chatty.models.user import User


class TestCreateUser:
    """Test cases for the create user endpoint."""

    def test_create_user_success(self, client_with_clean_db, db_session):
        """Test successful user creation with valid data."""
        user_data = {
            "name": "John Doe",
            "handle": "johndoe"
        }
        
        response = client_with_clean_db.post("/users/", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == "John Doe"
        assert data["handle"] == "johndoe"
        assert "created_date" in data
        assert "last_updated_date" in data
        
        # Verify user was actually created in database
        user = db_session.query(User).filter(User.handle == "johndoe").first()
        assert user is not None
        assert user.name == "John Doe"
        assert user.handle == "johndoe"

    def test_create_user_duplicate_handle(self, client_with_clean_db):
        """Test creating user with duplicate handle returns 409 conflict."""
        # Create first user
        user_data = {
            "name": "John Doe",
            "handle": "johndoe"
        }
        response = client_with_clean_db.post("/users/", json=user_data)
        assert response.status_code == 201
        
        # Try to create second user with same handle
        duplicate_user_data = {
            "name": "Jane Doe",
            "handle": "johndoe"
        }
        response = client_with_clean_db.post("/users/", json=duplicate_user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "User with this handle already exists"

    def test_create_user_empty_name(self, client_with_clean_db):
        """Test creating user with empty name returns validation error."""
        user_data = {
            "name": "",
            "handle": "johndoe"
        }
        
        response = client_with_clean_db.post("/users/", json=user_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
