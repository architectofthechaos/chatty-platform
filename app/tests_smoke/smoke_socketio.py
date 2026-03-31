"""
Simple Socket.IO tests for sanity checking the real-time functionality.
"""
import pytest
import pytest_asyncio
import socketio
import asyncio
import uuid
import requests
from typing import Dict, Any
from requests.exceptions import RequestException

NEEDED_SLEEP = 0.5


class ChattyAPIClient:
    """API client for creating test data via REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API client."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_user(self, name: str, handle: str) -> Dict[str, Any]:
        """Create a test user and return the user data."""
        user_data = {"name": name, "handle": handle}
        response = self.session.post(f"{self.base_url}/users/", json=user_data)
        response.raise_for_status()
        return response.json()
    
    def create_chatroom(self, name: str) -> Dict[str, Any]:
        """Create a test chatroom and return the chatroom data."""
        chatroom_data = {"name": name}
        response = self.session.post(f"{self.base_url}/chatrooms/", json=chatroom_data)
        response.raise_for_status()
        return response.json()
    
    def post_message(self, message_text: str, user_id: str, chatroom_id: str) -> Dict[str, Any]:
        """Post a message and return the message data."""
        message_data = {
            "message_text": message_text,
            "user_id": user_id,
            "chatroom_id": chatroom_id
        }
        response = self.session.post(f"{self.base_url}/messages/", json=message_data)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Test if the API is running and healthy."""
        response = self.session.get(f"{self.base_url}/health/")
        response.raise_for_status()
        return response.json()


class SocketIOTestClient:
    """Simple Socket.IO test client for testing event handlers."""
    
    def __init__(self, server_url: str = "http://localhost:8000/socket.io"):
        """Initialize the Socket.IO test client."""
        self.server_url = server_url
        self.client = socketio.AsyncClient()
        self.received_events: Dict[str, list] = {}
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to the Socket.IO server."""
        try:
            await self.client.connect(self.server_url)
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the Socket.IO server."""
        if self.connected:
            await self.client.disconnect()
            self.connected = False
    
    def setup_event_handlers(self):
        """Set up event handlers to capture received events."""
        
        @self.client.event
        async def joined(data):
            """Handle joined event."""
            print(f"[DEBUG] Socket.IO client received 'joined' event: {data}")
            if 'joined' not in self.received_events:
                self.received_events['joined'] = []
            self.received_events['joined'].append(data)
        
        @self.client.event
        async def left(data):
            """Handle left event."""
            print(f"[DEBUG] Socket.IO client received 'left' event: {data}")
            if 'left' not in self.received_events:
                self.received_events['left'] = []
            self.received_events['left'].append(data)
        
        @self.client.event
        async def new_message(data):
            """Handle new_message event."""
            print(f"[DEBUG] Socket.IO client received 'new_message' event: {data}")
            if 'new_message' not in self.received_events:
                self.received_events['new_message'] = []
            self.received_events['new_message'].append(data)
        
        @self.client.event
        async def error(data):
            """Handle error event."""
            print(f"[DEBUG] Socket.IO client received 'error' event: {data}")
            if 'error' not in self.received_events:
                self.received_events['error'] = []
            self.received_events['error'].append(data)
    
    async def join_room(self, user_id: str, chatroom_id: str) -> bool:
        """Join a chatroom."""
        try:
            print(f"[DEBUG] Attempting to join room: user_id={user_id}, chatroom_id={chatroom_id}")
            await self.client.emit('join', {'user_id': user_id, 'chatroom_id': chatroom_id})
            print(f"[DEBUG] Successfully sent join request for chatroom {chatroom_id}")
            return True
        except Exception as e:
            print(f"[DEBUG] Failed to join room: {e}")
            return False
    
    async def leave_room(self, user_id: str, chatroom_id: str) -> bool:
        """Leave a chatroom."""
        try:
            await self.client.emit('leave', {'user_id': user_id, 'chatroom_id': chatroom_id})
            return True
        except Exception as e:
            print(f"Failed to leave room: {e}")
            return False
    
    def get_received_events(self, event_name: str) -> list:
        """Get received events for a specific event name."""
        return self.received_events.get(event_name, [])
    
    def clear_received_events(self):
        """Clear all received events."""
        self.received_events.clear()


@pytest.fixture
def api_client():
    """Fixture providing an API client for REST operations."""
    return ChattyAPIClient()


@pytest_asyncio.fixture
async def socketio_client():
    """Fixture providing a Socket.IO test client."""
    client = SocketIOTestClient()
    client.setup_event_handlers()
    
    # Connect to server
    connected = await client.connect()
    if not connected:
        pytest.skip("Socket.IO server not available - skipping Socket.IO tests")
    
    yield client
    
    # Clean up
    await client.disconnect()


def test_api_health_check(api_client):
    """Test that the API is healthy before running Socket.IO tests."""
    health_data = api_client.health_check()
    assert "status" in health_data
    assert health_data["status"] == "healthy"


async def test_socketio_connect_disconnect(socketio_client):
    """Test basic Socket.IO connection and disconnection."""
    # Connection should be established by fixture
    assert socketio_client.connected
    
    # Test disconnection
    await socketio_client.disconnect()
    assert not socketio_client.connected


async def test_socketio_join_leave_room_with_real_data(api_client, socketio_client):
    """Test joining and leaving a chatroom using real user and chatroom data."""
    # Create real test data via REST API
    user_data = api_client.create_user(
        name="Join Leave Test User",
        handle=f"join_leave_test_{str(uuid.uuid4()).replace('-', '')}"
    )
    user_id = user_data["id"]
    
    chatroom_data = api_client.create_chatroom(
        name=f"join_leave_test_room_{str(uuid.uuid4()).replace('-', '')}"
    )
    chatroom_id = chatroom_data["id"]
    
    # Test joining a room
    success = await socketio_client.join_room(user_id, chatroom_id)
    assert success
    
    # Wait a bit for the event to be processed
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received a 'joined' event
    joined_events = socketio_client.get_received_events('joined')
    assert len(joined_events) == 1
    assert joined_events[0]['chatroom_id'] == chatroom_id
    
    # Test leaving the room
    success = await socketio_client.leave_room(user_id, chatroom_id)
    assert success
    
    # Wait a bit for the event to be processed
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received a 'left' event
    left_events = socketio_client.get_received_events('left')
    assert len(left_events) == 1
    assert left_events[0]['chatroom_id'] == chatroom_id


async def test_socketio_join_leave_room_with_uuid_data(socketio_client):
    """Test joining and leaving a chatroom using UUID strings (original behavior)."""
    user_id = str(uuid.uuid4())
    chatroom_id = str(uuid.uuid4())
    
    # Test joining a room
    success = await socketio_client.join_room(user_id, chatroom_id)
    assert success
    
    # Wait a bit for the event to be processed
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received a 'joined' event
    joined_events = socketio_client.get_received_events('joined')
    assert len(joined_events) == 1
    assert joined_events[0]['chatroom_id'] == chatroom_id
    
    # Test leaving the room
    success = await socketio_client.leave_room(user_id, chatroom_id)
    assert success
    
    # Wait a bit for the event to be processed
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received a 'left' event
    left_events = socketio_client.get_received_events('left')
    assert len(left_events) == 1
    assert left_events[0]['chatroom_id'] == chatroom_id


async def test_socketio_join_room_validation(socketio_client):
    """Test that join room validates required fields."""
    # Test joining without user_id
    success = await socketio_client.join_room("", str(uuid.uuid4()))
    assert success  # The emit succeeds, but server should send error
    
    # Wait for error event
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received an error
    error_events = socketio_client.get_received_events('error')
    assert len(error_events) >= 1
    assert 'user_id and chatroom_id are required' in error_events[0]['message']
    
    # Clear events and test without chatroom_id
    socketio_client.clear_received_events()
    
    success = await socketio_client.join_room(str(uuid.uuid4()), "")
    assert success  # The emit succeeds, but server should send error
    
    # Wait for error event
    await asyncio.sleep(NEEDED_SLEEP)
    
    # Check that we received an error
    error_events = socketio_client.get_received_events('error')
    assert len(error_events) >= 1
    assert 'user_id and chatroom_id are required' in error_events[0]['message']


async def test_socketio_message_flow_integration(api_client, socketio_client):
    """
    Test the integration between REST API message creation and Socket.IO events.
    This test creates a user, chatroom, joins the room, then posts a message via REST API
    and verifies that the Socket.IO client receives the new_message event.
    """
    # Create test data via REST API
    user_data = api_client.create_user(
        name="Socket Test User",
        handle=f"socket_test_{str(uuid.uuid4()).replace('-', '')}"
    )
    user_id = user_data["id"]
    
    chatroom_data = api_client.create_chatroom(
        name=f"socket_test_room_{str(uuid.uuid4()).replace('-', '')}"
    )
    chatroom_id = chatroom_data["id"]
    
    # Join the chatroom via Socket.IO
    success = await socketio_client.join_room(user_id, chatroom_id)
    assert success
    
    # Wait for join confirmation
    await asyncio.sleep(NEEDED_SLEEP)
    joined_events = socketio_client.get_received_events('joined')
    print(f"[DEBUG] After join wait, received {len(joined_events)} 'joined' events")
    assert len(joined_events) == 1
    
    # Post a message via REST API
    print(f"[DEBUG] Posting message via REST API to chatroom {chatroom_id}")
    created_message = api_client.post_message(
        message_text="Hello from Socket.IO test!",
        user_id=user_id,
        chatroom_id=chatroom_id
    )
    print(f"[DEBUG] Message posted successfully, ID: {created_message['id']}")
    
    # Wait for Socket.IO event
    print(f"[DEBUG] Waiting {NEEDED_SLEEP * 6} seconds for Socket.IO event...")
    await asyncio.sleep(NEEDED_SLEEP * 6)
    
    # Check that we received the new_message event
    new_message_events = socketio_client.get_received_events('new_message')
    print(f"[DEBUG] After message wait, received {len(new_message_events)} 'new_message' events")
    print(f"[DEBUG] All received events: {socketio_client.received_events}")
    assert len(new_message_events) == 1
    
    received_message = new_message_events[0]
    assert received_message['id'] == created_message['id']
    assert received_message['message_text'] == "Hello from Socket.IO test!"
    assert received_message['user_id'] == user_id
    assert received_message['chatroom_id'] == chatroom_id
