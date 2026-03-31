"""
Hello world endpoints.
"""
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HelloResponse(BaseModel):
    """Hello response model."""
    message: str
    name: str


class HelloRequest(BaseModel):
    """Hello request model."""
    name: str


@router.get("/", response_model=HelloResponse)
async def hello_world() -> HelloResponse:
    """
    Hello world endpoint.
    
    Returns a simple hello world message.
    """
    return HelloResponse(
        message="Hello, World!",
        name="World",
    )

