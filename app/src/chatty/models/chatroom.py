"""
Chatroom database model.
"""
import re
from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from chatty.core.database import BaseModel


class Chatroom(BaseModel):
    """Chatroom model with name."""
    __tablename__ = "chatrooms"
    
    name = Column(String(100), nullable=False, unique=True)
    
    # Relationships
    chatroom_participants = relationship("ChatroomParticipant", back_populates="chatroom")
    
    def __init__(self, name: str, **kwargs):
        """
        Initialize Chatroom with validation.
        
        Args:
            name: Chatroom name (will be lowercased and validated)
            **kwargs: Additional arguments passed to parent
        """
        # Validate and normalize name
        normalized_name = self._validate_and_normalize_name(name)
        
        super().__init__(
            name=normalized_name,
            **kwargs
        )
    
    @staticmethod
    def _validate_and_normalize_name(name: str) -> str:
        """
        Validate and normalize chatroom name.
        
        Args:
            name: Raw name input
            
        Returns:
            str: Normalized name (lowercase)
            
        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError("Name cannot be empty")
        
        # Convert to lowercase
        normalized_name = name.lower().strip()
        
        # Validate format: only letters, numbers, and underscores
        if not re.match(r'^[a-z0-9_]+$', normalized_name):
            raise ValueError(
                "Name can only contain lowercase letters, numbers, and underscores"
            )
        
        # Check length
        if len(normalized_name) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        
        if len(normalized_name) < 1:
            raise ValueError("Name must be at least 1 character")
        
        return normalized_name
    
    def update_name(self, new_name: str) -> None:
        """
        Update chatroom name with validation.
        
        Args:
            new_name: New name value
            
        Raises:
            ValueError: If name is invalid
        """
        self.name = self._validate_and_normalize_name(new_name)
    
    def __repr__(self) -> str:
        """String representation of Chatroom."""
        return f"<Chatroom(id={self.id}, name='{self.name}')>"
