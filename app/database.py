from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create engine with connection pooling settings for better performance
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Number of connections to maintain in the pool
    max_overflow=30,  # Number of connections beyond pool_size before blocking
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()  # Rollback on error
        raise
    finally:
        db.close()
