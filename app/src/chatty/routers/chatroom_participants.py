"""
Chatroom participant management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from chatty.core.database import get_db
from chatty.models.chatroom_participant import ChatroomParticipant
from chatty.models.user import User
from chatty.models.chatroom import Chatroom
from chatty.schemas.chatroom_participant import (
    ChatroomParticipantCreateRequest,
    ChatroomParticipantResponse,
    DeleteResponse,
)

router = APIRouter()


@router.post("/", response_model=ChatroomParticipantResponse, status_code=status.HTTP_201_CREATED)
async def create_chatroom_participant(
    participant_data: ChatroomParticipantCreateRequest,
    db: Session = Depends(get_db)
) -> ChatroomParticipantResponse:
    """
    Add a user to a chatroom as a participant.
    
    Args:
        participant_data: Participant creation data
        db: Database session
        
    Returns:
        ChatroomParticipantResponse: Created participant data
        
    Raises:
        HTTPException: 404 if user or chatroom not found, 409 if already a participant
    """
    # Verify user exists
    user = db.query(User).filter(User.id == participant_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify chatroom exists
    chatroom = db.query(Chatroom).filter(Chatroom.id == participant_data.chatroom_id).first()
    if not chatroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom not found"
        )
    
    try:
        # Create new participant
        db_participant = ChatroomParticipant(
            user_id=participant_data.user_id,
            chatroom_id=participant_data.chatroom_id
        )
        
        db.add(db_participant)
        db.commit()
        db.refresh(db_participant)
        
        return ChatroomParticipantResponse.from_orm(db_participant)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a participant in this chatroom"
        )


@router.delete("/{participant_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_chatroom_participant(
    participant_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Remove a user from a chatroom.
    
    Args:
        participant_id: Participant UUID
        db: Database session
        
    Returns:
        DeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException: 404 if participant not found
    """
    participant = db.query(ChatroomParticipant).filter(
        ChatroomParticipant.id == participant_id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatroom participant not found"
        )
    
    db.delete(participant)
    db.commit()
    
    return DeleteResponse(deleted=True)


# TODO - Confirm need for this endpoint
@router.delete("/user/{user_id}/chatroom/{chatroom_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def remove_user_from_chatroom(
    user_id: str,
    chatroom_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Remove a user from a chatroom by user and chatroom IDs.
    
    Args:
        user_id: User UUID
        chatroom_id: Chatroom UUID
        db: Database session
        
    Returns:
        DeleteResponse: Deletion confirmation
        
    Raises:
        HTTPException: 404 if participant not found
    """
    participant = db.query(ChatroomParticipant).filter(
        ChatroomParticipant.user_id == user_id,
        ChatroomParticipant.chatroom_id == chatroom_id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a participant in this chatroom"
        )
    
    db.delete(participant)
    db.commit()
    
    return DeleteResponse(deleted=True)
