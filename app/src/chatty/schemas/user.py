"""
User Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""
    name: str = Field(..., min_length=1, max_length=255, description="User's display name")
    handle: str = Field(..., min_length=1, max_length=50, description="User's unique handle")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('handle')
    def validate_handle(cls, v):
        """Validate handle field."""
        if not v or not v.strip():
            raise ValueError('Handle cannot be empty')
        
        # Convert to lowercase and strip whitespace
        normalized = v.lower().strip()
        
        # Check for valid characters (letters, numbers, underscores only)
        import re
        if not re.match(r'^[a-z0-9_]+$', normalized):
            raise ValueError(
                'Handle can only contain lowercase letters, numbers, and underscores'
            )
        
        return normalized


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""
    name: str = Field(None, min_length=1, max_length=255, description="User's display name")
    handle: str = Field(None, min_length=1, max_length=50, description="User's unique handle")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v
    
    @validator('handle')
    def validate_handle(cls, v):
        """Validate handle field."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Handle cannot be empty')
            
            # Convert to lowercase and strip whitespace
            normalized = v.lower().strip()
            
            # Check for valid characters (letters, numbers, underscores only)
            import re
            if not re.match(r'^[a-z0-9_]+$', normalized):
                raise ValueError(
                    'Handle can only contain lowercase letters, numbers, and underscores'
                )
            
            return normalized
        return v


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's display name")
    handle: str = Field(..., description="User's unique handle")
    created_date: datetime = Field(..., description="When the user was created")
    last_updated_date: datetime = Field(..., description="When the user was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserListResponse(BaseModel):
    """Response schema for listing users."""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")


class UserChatroomResponse(BaseModel):
    """Response schema for user's chatroom participation."""
    id: str = Field(..., description="Unique chatroom identifier")
    name: str = Field(..., description="Chatroom name")
    created_date: datetime = Field(..., description="When the chatroom was created")
    last_updated_date: datetime = Field(..., description="When the chatroom was last updated")
    joined_date: datetime = Field(..., description="When the user joined the chatroom")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserChatroomListResponse(BaseModel):
    """Response schema for listing user's chatrooms."""
    chatrooms: List[UserChatroomResponse] = Field(..., description="List of chatrooms the user participates in")
    total: int = Field(..., description="Total number of chatrooms")


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
