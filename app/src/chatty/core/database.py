"""
Database configuration and session management.
"""
import os
import uuid
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.types import TypeDecorator, CHAR

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./chatty.db")

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


# TODO - Probs best to move to models folder
class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True,  default=lambda: str(uuid.uuid4()))
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_date = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
