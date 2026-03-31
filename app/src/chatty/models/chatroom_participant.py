"""
ChatroomParticipant database model.
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from chatty.core.database import BaseModel


class ChatroomParticipant(BaseModel):
    """ChatroomParticipant model linking users to chatrooms."""
    __tablename__ = "chatroom_participants"
    
    # Foreign keys
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    chatroom_id = Column(String(36), ForeignKey("chatrooms.id"), nullable=False)
    
    # Unique constraint to prevent duplicate participants
    __table_args__ = (
        UniqueConstraint('user_id', 'chatroom_id', name='unique_user_chatroom'),
    )
    
    # Relationships
    user = relationship("User", back_populates="chatroom_participants")
    chatroom = relationship("Chatroom", back_populates="chatroom_participants")
    
    def __init__(self, user_id: str, chatroom_id: str, **kwargs):
        """
        Initialize ChatroomParticipant.
        
        Args:
            user_id: User UUID
            chatroom_id: Chatroom UUID
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(
            user_id=user_id,
            chatroom_id=chatroom_id,
            **kwargs
        )
    
    def __repr__(self) -> str:
        """String representation of ChatroomParticipant."""
        return f"<ChatroomParticipant(id={self.id}, user_id='{self.user_id}', chatroom_id='{self.chatroom_id}')>"
