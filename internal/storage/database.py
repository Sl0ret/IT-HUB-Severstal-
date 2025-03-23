from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from ..logger.logger import logger
from config.config import settings
from .in_memory_storage import InMemoryStorage
from .database_storage import DatabaseStorage



DATABASE_URL = settings.database_url

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base = declarative_base()
    logger.info("Database engine initialized")
except SQLAlchemyError as e:
    logger.critical("Database connection failed: %s", str(e))
    raise

def get_storage():
    try:
        if settings.storage_type == "in_memory":
            logger.debug("Using InMemoryStorage")
            return InMemoryStorage()
        else:
            logger.debug("Initializing DatabaseStorage")
            db = SessionLocal()
            return DatabaseStorage(db)
    except SQLAlchemyError as e:
        logger.error("Database session error: %s", str(e))
        raise
    except Exception as e:
        logger.critical("Storage initialization failed: %s", str(e))
        raise