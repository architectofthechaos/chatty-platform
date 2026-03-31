"""
Message Pydantic schemas for API requests and responses.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class MessageCreateRequest(BaseModel):
    """Request schema for creating a message."""
    message_text: str = Field(..., min_length=1, max_length=1024, description="Message content")
    user_id: str = Field(..., description="ID of the user sending the message")
    chatroom_id: str = Field(..., description="ID of the chatroom where message is sent")
    is_reply: bool = Field(False, description="Whether this is a reply to another message")
    parent_message_id: Optional[str] = Field(None, description="ID of parent message (required if is_reply=True)")
    
    @validator('message_text')
    def validate_message_text(cls, v):
        """Validate message text field."""
        if not v or not v.strip():
            raise ValueError('Message text cannot be empty or only whitespace')
        return v.strip()
    
    @validator('parent_message_id')
    def validate_parent_message_id(cls, v, values):
        """Validate parent_message_id based on is_reply."""
        is_reply = values.get('is_reply', False)
        
        if is_reply and not v:
            raise ValueError('parent_message_id is required when is_reply is True')
        
        if not is_reply and v:
            raise ValueError('parent_message_id should only be set when is_reply is True')
        
        return v


class MessageResponse(BaseModel):
    """Response schema for message data."""
    id: str = Field(..., description="Unique message identifier")
    message_text: str = Field(..., description="Message content")
    user_id: str = Field(..., description="ID of the user who sent the message")
    chatroom_id: str = Field(..., description="ID of the chatroom where message was sent")
    is_reply: bool = Field(..., description="Whether this is a reply to another message")
    parent_message_id: Optional[str] = Field(None, description="ID of parent message")
    created_date: datetime = Field(..., description="When the message was created")
    last_updated_date: datetime = Field(..., description="When the message was last updated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response schema for listing messages."""
    messages: List[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""
    deleted: bool = Field(..., description="Whether the deletion was successful")
