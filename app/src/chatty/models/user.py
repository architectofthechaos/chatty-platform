"""
User database model.
"""
import re
from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from chatty.core.database import BaseModel


class User(BaseModel):
    """User model with name and handle."""
    __tablename__ = "users"
    
    name = Column(String(255), nullable=False)
    handle = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    chatroom_participants = relationship("ChatroomParticipant", back_populates="user")
    
    def __init__(self, name: str, handle: str, **kwargs):
        """
        Initialize User with validation.
        
        Args:
            name: User's display name
            handle: User's unique handle (will be lowercased and validated)
            **kwargs: Additional arguments passed to parent
        """
        # Validate and normalize handle
        normalized_handle = self._validate_and_normalize_handle(handle)
        
        super().__init__(
            name=name,
            handle=normalized_handle,
            **kwargs
        )
    
    @staticmethod
    def _validate_and_normalize_handle(handle: str) -> str:
        """
        Validate and normalize user handle.
        
        Args:
            handle: Raw handle input
            
        Returns:
            str: Normalized handle (lowercase)
            
        Raises:
            ValueError: If handle is invalid
        """
        if not handle:
            raise ValueError("Handle cannot be empty")
        
        # Convert to lowercase
        normalized_handle = handle.lower().strip()
        
        # Validate format: only letters, numbers, and underscores
        if not re.match(r'^[a-z0-9_]+$', normalized_handle):
            raise ValueError(
                "Handle can only contain lowercase letters, numbers, and underscores"
            )
        
        # Check length
        if len(normalized_handle) > 50:
            raise ValueError("Handle cannot exceed 50 characters")
        
        if len(normalized_handle) < 1:
            raise ValueError("Handle must be at least 1 character")
        
        return normalized_handle
    
    def update_handle(self, new_handle: str) -> None:
        """
        Update user handle with validation.
        
        Args:
            new_handle: New handle value
            
        Raises:
            ValueError: If handle is invalid
        """
        self.handle = self._validate_and_normalize_handle(new_handle)
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, name='{self.name}', handle='{self.handle}')>"
