import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and handles cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as err:
        logger.error(f"Database session error: {err}")
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Utility function to test database connectivity.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except OperationalError as err:
        logger.warning(f"Database operational error during connectivity check: {err}")
        return False
    except Exception as err:
        logger.error(f"Unexpected database connection error: {err}")
        return False
