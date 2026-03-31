"""
User management endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from chatty.core.database import get_db
from chatty.models.user import User
from chatty.models.chatroom_participant import ChatroomParticipant
from chatty.models.chatroom import Chatroom
from chatty.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    UserChatroomResponse,
    UserChatroomListResponse,
    DeleteResponse,
)

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Create a new user.
    
    Args:
        user_data: User creation data
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: 409 if handle already exists, 400 for validation errors
    """
    try:
        # Create new user
        db_user = User(
            name=user_data.name,
            handle=user_data.handle
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse.from_orm(db_user)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this handle already exists"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get a user by ID.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        UserResponse: User data
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: Session = Depends(get_db)
) -> UserListResponse:
    """
    List all users.
    
    Args:
        db: Database session
        
    Returns:
        UserListResponse: List of all users
    """
    users = db.query(User).all()
    
    user_responses = [UserResponse.from_orm(user) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=len(user_responses)
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update a user.
    
    Args:
        user_id: User UUID
        user_data: User update data
        db: Database session
        
    Returns:
        UserResponse: Updated user data
        
    Raises:
        HTTPException: 404 if user not found, 409 if handle conflict, 400 for validation errors
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Update fields if provided
        if user_data.name is not None:
            user.name = user_data.name
        
        if user_data.handle is not None:
            user.update_handle(user_data.handle)
        
        db.commit()
        db.refresh(user)
        
        return UserResponse.from_orm(user)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this handle already exists"
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Delete a user.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        DeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return DeleteResponse(deleted=True)


@router.get("/{user_id}/chatrooms", response_model=UserChatroomListResponse)
async def get_user_chatrooms(
    user_id: str,
    db: Session = Depends(get_db)
) -> UserChatroomListResponse:
    """
    Get all chatrooms for a user.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        UserChatroomListResponse: List of chatrooms the user participates in
        
    Raises:
        HTTPException: 404 if user not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all chatrooms for this user with chatroom details
    participants = db.query(ChatroomParticipant, Chatroom).join(
        Chatroom, ChatroomParticipant.chatroom_id == Chatroom.id
    ).filter(
        ChatroomParticipant.user_id == user_id
    ).all()
    
    # Build response objects
    chatroom_responses = []
    for participant, chatroom in participants:
        chatroom_response = UserChatroomResponse(
            id=chatroom.id,
            name=chatroom.name,
            created_date=chatroom.created_date,
            last_updated_date=chatroom.last_updated_date,
            joined_date=participant.created_date
        )
        chatroom_responses.append(chatroom_response)
    
    return UserChatroomListResponse(
        chatrooms=chatroom_responses,
        total=len(chatroom_responses)
    )
