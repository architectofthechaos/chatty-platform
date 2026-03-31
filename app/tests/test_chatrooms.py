"""
Tests for chatroom management endpoints.
"""
import pytest
import uuid
from chatty.models.chatroom import Chatroom


class TestCreateChatroom:
    """Test cases for the create chatroom endpoint."""

    def test_create_chatroom_success(self, client_with_clean_db, db_session):
        """Test successful chatroom creation with valid data."""
        chatroom_data = {
            "name": "general"
        }
        
        response = client_with_clean_db.post("/chatrooms/", json=chatroom_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == "general"
        assert "created_date" in data
        assert "last_updated_date" in data
        
        # Verify chatroom was actually created in database
        chatroom = db_session.query(Chatroom).filter(Chatroom.name == "general").first()
        assert chatroom is not None
        assert chatroom.name == "general"


    def test_create_chatroom_duplicate_name(self, client_with_clean_db):
        """Test creating chatroom with duplicate name returns 409 conflict."""
        # Create first chatroom
        chatroom_data = {
            "name": "general"
        }
        response = client_with_clean_db.post("/chatrooms/", json=chatroom_data)
        assert response.status_code == 201
        
        # Try to create second chatroom with same name
        duplicate_chatroom_data = {
            "name": "general"
        }
        response = client_with_clean_db.post("/chatrooms/", json=duplicate_chatroom_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"] == "Chatroom with this name already exists"

    def test_create_chatroom_invalid_name_empty(self, client_with_clean_db):
        """Test creating chatroom with empty name returns validation error."""
        chatroom_data = {
            "name": ""
        }
        
        response = client_with_clean_db.post("/chatrooms/", json=chatroom_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


class TestUpdateChatroom:
    """Test cases for the update chatroom endpoint."""

    def test_update_chatroom_success(self, client_with_clean_db, db_session):
        """Test successful chatroom update with valid data."""
        # First create a chatroom
        chatroom_data = {
            "name": "general"
        }
        create_response = client_with_clean_db.post("/chatrooms/", json=chatroom_data)
        assert create_response.status_code == 201
        chatroom_id = create_response.json()["id"]
        
        # Update the chatroom
        update_data = {
            "name": "general_updated"
        }
        response = client_with_clean_db.put(f"/chatrooms/{chatroom_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["id"] == chatroom_id
        assert data["name"] == "general_updated"
        assert "created_date" in data
        assert "last_updated_date" in data
        
        # Verify chatroom was actually updated in database
        chatroom = db_session.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
        assert chatroom is not None
        assert chatroom.name == "general_updated"
