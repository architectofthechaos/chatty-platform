"""
Smoke test for Chatty API using pytest.
"""

import json
import time
from typing import Dict, Any, Optional
import pytest
import requests
from requests.exceptions import RequestException
import uuid


class ChattyAPIClient:
    """API client for Chatty API smoke tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data for POST/PUT requests
            
        Returns:
            Response JSON data
            
        Raises:
            RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except RequestException as e:
            # Let pytest handle the error reporting
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Test if the API is running and healthy."""
        return self.make_request("GET", "/health/")
    
    def create_user(self, name: str, handle: str) -> Dict[str, Any]:
        """Create a test user and return the user data."""
        user_data = {"name": name, "handle": handle}
        return self.make_request("POST", "/users/", user_data)
    
    def create_chatroom(self, name: str) -> Dict[str, Any]:
        """Create a test chatroom and return the chatroom data."""
        chatroom_data = {"name": name}
        return self.make_request("POST", "/chatrooms/", chatroom_data)
    
    def post_message(self, message_text: str, user_id: str, chatroom_id: str, is_reply: bool = False, parent_message_id: Optional[str] = None) -> Dict[str, Any]:
        """Post a message and return the message data."""
        message_data = {
            "message_text": message_text,
            "user_id": user_id,
            "chatroom_id": chatroom_id,
            "is_reply": is_reply
        }
        if parent_message_id:
            message_data["parent_message_id"] = parent_message_id
        return self.make_request("POST", "/messages/", message_data)
    
    def get_messages_for_chatroom(self, chatroom_id: str) -> Dict[str, Any]:
        """Get all messages for a chatroom."""
        return self.make_request("GET", f"/messages/chatroom/{chatroom_id}")
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user."""
        return self.make_request("DELETE", f"/users/{user_id}")
    
    def delete_chatroom(self, chatroom_id: str) -> Dict[str, Any]:
        """Delete a chatroom."""
        return self.make_request("DELETE", f"/chatrooms/{chatroom_id}")
    
    def delete_message(self, message_id: str) -> Dict[str, Any]:
        """Delete a message."""
        return self.make_request("DELETE", f"/messages/{message_id}")


# Pytest fixtures
@pytest.fixture
def api_client():
    """Fixture providing an API client."""
    return ChattyAPIClient()


@pytest.fixture
def test_data():
    """Fixture providing test data."""
    return {
        "user": {
            "name": f"Smoke Test User {str(uuid.uuid4())}",
            "handle": f"smoke_test_user_{str(uuid.uuid4()).replace('-', '')}"
        },
        "chatroom": {
            "name": f"smoke_test_chatroom_{str(uuid.uuid4()).replace('-', '')}"
        },
        "messages": [
            "Hello! This is the first smoke test message.",
            "This is the second smoke test message. Testing message persistence!"
        ]
    }


def test_smoke_test_full_flow(api_client, test_data):
    """
    Test the complete smoke test flow in one test.
    1. Creating a user
    2. Creating a chatroom
    3. Posting two messages from that user to the chatroom
    4. Getting messages from the chatroom to confirm we get those two messages back
    """
    
    # Step 1: Health check
    api_client.health_check()
    
    # Step 2: Create user
    user_data = api_client.create_user(
        name=test_data["user"]["name"],
        handle=test_data["user"]["handle"]
    )
    user_id = user_data["id"]
    
    # Step 3: Create chatroom
    chatroom_data = api_client.create_chatroom(
        name=test_data["chatroom"]["name"]
    )
    chatroom_id = chatroom_data["id"]
    
    # Step 4: Post messages
    message_ids = []
    for message_text in test_data["messages"]:
        message_data = api_client.post_message(
            message_text=message_text,
            user_id=user_id,
            chatroom_id=chatroom_id
        )
        message_ids.append(message_data["id"])
        time.sleep(0.5)  # Small delay to ensure different timestamps
    
    # Step 5: Get messages and verify
    response = api_client.get_messages_for_chatroom(chatroom_id)
    actual_messages = sorted(response["messages"], key=lambda x: x["created_date"])
    
    assert len(actual_messages) == len(test_data["messages"])
    
    for expected_text, actual_message in zip(test_data["messages"], actual_messages):
        assert actual_message["message_text"] == expected_text
        assert actual_message["user_id"] == user_id
        assert actual_message["chatroom_id"] == chatroom_id
