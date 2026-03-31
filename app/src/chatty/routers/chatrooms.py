"""
Chatroom management endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from chatty.core.database import get_db
from chatty.models.chatroom import Chatroom
from chatty.models.chatroom_participant import ChatroomParticipant
from chatty.models.user import User
from chatty.schemas.chatroom import (
    ChatroomCreateRequest,
    ChatroomUpdateRequest,
    ChatroomResponse,
    ChatroomListResponse,
    ChatroomUserResponse,
    ChatroomUserListResponse,
    DeleteResponse,
)

router = APIRouter()


@router.post("/", response_model=ChatroomResponse, status_code=status.HTTP_201_CREATED)
async def create_chatroom(
    chatroom_data: ChatroomCreateRequest,
    db: Session = Depends(get_db)
) -> ChatroomResponse:
    """
    Create a new chatroom.
    
    Args:
        chatroom_data: Chatroom creation data
        db: Database session
        
    Returns:
        ChatroomResponse: Created chatroom data
        
    Raises:
        HTTPException: 409 if name already exists, 400 for validation errors
    """
    try:
        # Create new chatroom
        db_chatroom = Chatroom(
            name=chatroom_data.name
        )
        
        db.add(db_chatroom)
        db.commit()
        db.refresh(db_chatroom)
        
        return ChatroomResponse.from_orm(db_chatroom)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chatroom with this name already exists"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{chatroom_id}", response_model=ChatroomResponse)
async def get_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db)
) -> ChatroomResponse:
    """
    Get a chatroom by ID.
    
    Args:
        chatroom_id: Chatroom UUID
        db: Database session
        
    Returns:
        ChatroomResponse: Chatroom data
        
    Raises:
        HTTPException: 404 if chatroom not found
    """
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    return ChatroomResponse.from_orm(chatroom)


@router.get("/", response_model=ChatroomListResponse)
async def list_chatrooms(
    db: Session = Depends(get_db)
) -> ChatroomListResponse:
    """
    List all chatrooms.
    
    Args:
        db: Database session
        
    Returns:
        ChatroomListResponse: List of all chatrooms
    """
    chatrooms = db.query(Chatroom).all()
    
    chatroom_responses = [ChatroomResponse.from_orm(chatroom) for chatroom in chatrooms]
    
    return ChatroomListResponse(
        chatrooms=chatroom_responses,
        total=len(chatroom_responses)
    )


@router.put("/{chatroom_id}", response_model=ChatroomResponse)
async def update_chatroom(
    chatroom_id: str,
    chatroom_data: ChatroomUpdateRequest,
    db: Session = Depends(get_db)
) -> ChatroomResponse:
    """
    Update a chatroom.
    
    Args:
        chatroom_id: Chatroom UUID
        chatroom_data: Chatroom update data
        db: Database session
        
    Returns:
        ChatroomResponse: Updated chatroom data
        
    Raises:
        HTTPException: 404 if chatroom not found, 409 if name conflict, 400 for validation errors
    """
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    try:
        # Update fields if provided
        if chatroom_data.name is not None:
            chatroom.update_name(chatroom_data.name)
        
        db.commit()
        db.refresh(chatroom)
        
        return ChatroomResponse.from_orm(chatroom)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chatroom with this name already exists"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{chatroom_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_chatroom(
    chatroom_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Delete a chatroom.
    
    Args:
        chatroom_id: Chatroom UUID
        db: Database session
        
    Returns:
        DeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException: 404 if chatroom not found
    """
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    db.delete(chatroom)
    db.commit()
    
    return DeleteResponse(deleted=True)


@router.get("/{chatroom_id}/users", response_model=ChatroomUserListResponse)
async def get_chatroom_users(
    chatroom_id: str,
    db: Session = Depends(get_db)
) -> ChatroomUserListResponse:
    """
    Get all users in a chatroom.
    
    Args:
        chatroom_id: Chatroom UUID
        db: Database session
        
    Returns:
        ChatroomUserListResponse: List of users in the chatroom
        
    Raises:
        HTTPException: 404 if chatroom not found
    """
    # Verify chatroom exists
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    # Get all participants for this chatroom with user details
    participants = db.query(ChatroomParticipant, User).join(
        User, ChatroomParticipant.user_id == User.id
    ).filter(
        ChatroomParticipant.chatroom_id == chatroom_id
    ).all()
    
    # Build response objects
    user_responses = []
    for participant, user in participants:
        user_response = ChatroomUserResponse(
            id=user.id,
            name=user.name,
            handle=user.handle,
            created_date=user.created_date,
            last_updated_date=user.last_updated_date,
            joined_date=participant.created_date
        )
        user_responses.append(user_response)
    
    return ChatroomUserListResponse(
        users=user_responses,
        total=len(user_responses)
    )
