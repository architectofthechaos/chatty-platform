"""
Message management endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from chatty.core.database import get_db
from chatty.core.logging import get_logger
from chatty.models.message import Message
from chatty.models.user import User
from chatty.models.chatroom import Chatroom
from chatty.schemas.message import (
    MessageCreateRequest,
    MessageResponse,
    MessageListResponse,
    DeleteResponse,
)

router = APIRouter()
logger = get_logger("messages")

# Import Socket.IO server from main module
# This will be set by main.py after the server is created
sio = None

def set_socketio_server(socketio_server):
    """Set the Socket.IO server instance for use in message endpoints."""
    global sio
    sio = socketio_server


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreateRequest,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Create a new message.
    
    Args:
        message_data: Message creation data
        db: Database session
        
    Returns:
        MessageResponse: Created message data
        
    Raises:
        HTTPException: 404 if user or chatroom not found, 400 for validation errors
    """
    try:
        # Validate that user exists
        user = db.query(User).filter(User.id == message_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate that chatroom exists
        chatroom = db.query(Chatroom).filter(Chatroom.id == message_data.chatroom_id).first()
        if not chatroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatroom not found"
            )
        
        # If this is a reply, validate that parent message exists
        if message_data.is_reply and message_data.parent_message_id:
            parent_message = db.query(Message).filter(
                Message.id == message_data.parent_message_id
            ).first()
            if not parent_message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent message not found"
                )
        
        # Create new message
        db_message = Message(
            message_text=message_data.message_text,
            user_id=message_data.user_id,
            chatroom_id=message_data.chatroom_id,
            is_reply=message_data.is_reply,
            parent_message_id=message_data.parent_message_id
        )
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Create response object
        message_response = MessageResponse.from_orm(db_message)
        
        # Emit new_message event to the chatroom via Socket.IO
        if sio:
            try:
                # Convert the response to dict for Socket.IO emission with JSON serialization
                serialized_message = message_response.model_dump(mode='json')
                await sio.emit('new_message', serialized_message, room=serialized_message['chatroom_id'])
                logger.info(f"Emitted new_message event to chatroom {serialized_message['chatroom_id']}")
            except Exception as e:
                # TODO: Implement proper error handling for Socket.IO emission
                logger.error(f"Error emitting new_message event: {e}")
        
        return message_response
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Get a message by ID.
    
    Args:
        message_id: Message UUID
        db: Database session
        
    Returns:
        MessageResponse: Message data
        
    Raises:
        HTTPException: 404 if message not found
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MessageResponse.from_orm(message)


@router.get("/chatroom/{chatroom_id}", response_model=MessageListResponse)
async def list_messages_by_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db)
) -> MessageListResponse:
    """
    List all messages for a specific chatroom.
    
    Args:
        chatroom_id: Chatroom UUID
        db: Database session
        
    Returns:
        MessageListResponse: List of messages in the chatroom
        
    Raises:
        HTTPException: 404 if chatroom not found
    """
    # Validate that chatroom exists
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    messages = db.query(Message).filter(Message.chatroom_id == chatroom_id).all()
    
    message_responses = [MessageResponse.from_orm(message) for message in messages]
    
    return MessageListResponse(
        messages=message_responses,
        total=len(message_responses)
    )


@router.delete("/{message_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Delete a message.
    
    Args:
        message_id: Message UUID
        db: Database session
        
    Returns:
        DeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException: 404 if message not found
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    db.delete(message)
    db.commit()
    
    return DeleteResponse(deleted=True)
