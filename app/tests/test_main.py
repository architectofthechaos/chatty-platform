"""
Tests for the main FastAPI application.
"""
import pytest


def test_root_endpoint(client) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Chatty Backend!"}


def test_health_check(client) -> None:
    """Test the health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"

def test_hello_world(client) -> None:
    """Test the hello world endpoint."""
    response = client.get("/hello/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, World!"
    assert data["name"] == "World"

