"""
ChatroomParticipant Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator


class ChatroomParticipantCreateRequest(BaseModel):
    """Request schema for creating a chatroom participant."""
    user_id: str = Field(..., description="User UUID")
    chatroom_id: str = Field(..., description="Chatroom UUID")
    
    @validator('user_id', 'chatroom_id')
    def validate_uuids(cls, v):
        """Validate UUID format."""
        if not v or not v.strip():
            raise ValueError('UUID cannot be empty')
        
        # Basic UUID format validation (36 characters with dashes)
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v.lower()):
            raise ValueError('Invalid UUID format')
        
        return v.strip()


class ChatroomParticipantResponse(BaseModel):
    """Response schema for chatroom participant data."""
    id: str = Field(..., description="Unique participant identifier")
    user_id: str = Field(..., description="User UUID")
    chatroom_id: str = Field(..., description="Chatroom UUID")
    created_date: datetime = Field(..., description="When the participant was added")
    last_updated_date: datetime = Field(..., description="When the participant was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChatroomParticipantListResponse(BaseModel):
    """Response schema for listing chatroom participants."""
    participants: List[ChatroomParticipantResponse] = Field(..., description="List of participants")
    total: int = Field(..., description="Total number of participants")


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
