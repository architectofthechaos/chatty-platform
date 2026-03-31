"""
Chatroom Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator


class ChatroomCreateRequest(BaseModel):
    """Request schema for creating a chatroom."""
    name: str = Field(..., min_length=1, max_length=100, description="Chatroom name")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Convert to lowercase and strip whitespace
        normalized = v.lower().strip()
        
        # Check for valid characters (letters, numbers, underscores only)
        import re
        if not re.match(r'^[a-z0-9_]+$', normalized):
            raise ValueError(
                'Name can only contain lowercase letters, numbers, and underscores'
            )
        
        return normalized


class ChatroomUpdateRequest(BaseModel):
    """Request schema for updating a chatroom."""
    name: str = Field(None, min_length=1, max_length=100, description="Chatroom name")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            
            # Convert to lowercase and strip whitespace
            normalized = v.lower().strip()
            
            # Check for valid characters (letters, numbers, underscores only)
            import re
            if not re.match(r'^[a-z0-9_]+$', normalized):
                raise ValueError(
                    'Name can only contain lowercase letters, numbers, and underscores'
                )
            
            return normalized
        return v


class ChatroomResponse(BaseModel):
    """Response schema for chatroom data."""
    id: str = Field(..., description="Unique chatroom identifier")
    name: str = Field(..., description="Chatroom name")
    created_date: datetime = Field(..., description="When the chatroom was created")
    last_updated_date: datetime = Field(..., description="When the chatroom was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChatroomListResponse(BaseModel):
    """Response schema for listing chatrooms."""
    chatrooms: List[ChatroomResponse] = Field(..., description="List of chatrooms")
    total: int = Field(..., description="Total number of chatrooms")


class ChatroomUserResponse(BaseModel):
    """Response schema for chatroom's user participants."""
    id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's display name")
    handle: str = Field(..., description="User's unique handle")
    created_date: datetime = Field(..., description="When the user was created")
    last_updated_date: datetime = Field(..., description="When the user was last updated")
    joined_date: datetime = Field(..., description="When the user joined the chatroom")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChatroomUserListResponse(BaseModel):
    """Response schema for listing chatroom's users."""
    users: List[ChatroomUserResponse] = Field(..., description="List of users in the chatroom")
    total: int = Field(..., description="Total number of users")


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
