"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from chatty.main import app
from chatty.core.database import get_db, Base

# Hardcoded test database URL - simple and straightforward
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(test_session_factory):
    """Create a fresh database session for each test."""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_session_factory):
    """Create a test client with database dependency override."""
    def override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_clean_db(client, db_session):
    """Create a test client with a clean database - truncates all tables before each test."""
    # Truncate all tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    
    yield client
    
    # Clean up after test as well
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
