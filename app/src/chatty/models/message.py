"""
Message database model.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from chatty.core.database import BaseModel


class Message(BaseModel):
    """Message model with text content and relationships."""
    __tablename__ = "messages"
    
    message_text = Column(String(1024), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    chatroom_id = Column(String(36), ForeignKey("chatrooms.id"), nullable=False)
    is_reply = Column(Boolean, default=False, nullable=False)
    parent_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)
    
    # Create indexes for better query performance
    __table_args__ = (
        Index('ix_messages_user_id', 'user_id'),
        Index('ix_messages_chatroom_id', 'chatroom_id'),
        Index('ix_messages_parent_message_id', 'parent_message_id'),
    )
    
    def __init__(self, message_text: str, user_id: str, chatroom_id: str, 
                 is_reply: bool = False, parent_message_id: str = None, **kwargs):
        """
        Initialize Message with validation.
        
        Args:
            message_text: The message content (max 1024 chars)
            user_id: ID of the user who sent the message
            chatroom_id: ID of the chatroom where message was sent
            is_reply: Whether this is a reply to another message
            parent_message_id: ID of parent message (required if is_reply=True)
            **kwargs: Additional arguments passed to parent
            
        Raises:
            ValueError: If validation fails
        """
        # Validate message text
        self._validate_message_text(message_text)
        
        # Validate reply logic
        if is_reply and not parent_message_id:
            raise ValueError("parent_message_id is required when is_reply is True")
        
        if not is_reply and parent_message_id:
            raise ValueError("parent_message_id should only be set when is_reply is True")
        
        super().__init__(
            message_text=message_text,
            user_id=user_id,
            chatroom_id=chatroom_id,
            is_reply=is_reply,
            parent_message_id=parent_message_id,
            **kwargs
        )
    
    @staticmethod
    def _validate_message_text(message_text: str) -> None:
        """
        Validate message text.
        
        Args:
            message_text: Message content to validate
            
        Raises:
            ValueError: If message text is invalid
        """
        if not message_text:
            raise ValueError("Message text cannot be empty")
        
        if not message_text.strip():
            raise ValueError("Message text cannot be only whitespace")
        
        if len(message_text) > 1024:
            raise ValueError("Message text cannot exceed 1024 characters")
    
    def update_message_text(self, new_text: str) -> None:
        """
        Update message text with validation.
        
        Args:
            new_text: New message text
            
        Raises:
            ValueError: If new text is invalid
        """
        self._validate_message_text(new_text)
        self.message_text = new_text
    
    def __repr__(self) -> str:
        """String representation of Message."""
        return f"<Message(id={self.id}, user_id='{self.user_id}', chatroom_id='{self.chatroom_id}', is_reply={self.is_reply})>"
