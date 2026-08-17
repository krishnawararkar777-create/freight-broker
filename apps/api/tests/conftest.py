import pytest
from db.session import SessionLocal, engine, Base

@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh transactional database session for a test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
