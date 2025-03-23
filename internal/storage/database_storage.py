from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from .storage import StorageInterface
from ..models.schemas import RollStats, RollCreate, RollResponse
from .crud import create_roll, get_rolls, delete_roll, get_stats
from ..logger.logger import logger


class DatabaseStorage(StorageInterface):
    def __init__(self, db: Session):
        self.db = db
        logger.debug("DatabaseStorage initialized with session %s", id(db))

    def create_roll(self, roll: RollCreate) -> RollResponse:
        try:
            logger.info("Attempting to create roll: %s", roll.model_dump())
            result = create_roll(self.db, roll)
            logger.debug("Roll created successfully. ID: %d", result.id)
            return result
        except SQLAlchemyError as e:
            logger.error("Database error during roll creation: %s", str(e))
            raise
        except Exception as e:
            logger.critical("Unexpected error in create_roll: %s", str(e))
            raise

    def get_rolls(self, filters: Dict[str, Optional[str]]) -> List[RollResponse]:
        try:
            logger.info("Fetching rolls with filters: %s", filters)
            result = get_rolls(self.db, filters)
            logger.debug("Found %d rolls matching filters", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Database error in get_rolls: %s", str(e))
            raise
        except ValueError as e:
            logger.error("Invalid filter format: %s", str(e))
            raise
        except Exception as e:
            logger.critical("Unexpected error in get_rolls: %s", str(e))
            raise

    def delete_roll(self, roll_id: int) -> Optional[RollResponse]:
        try:
            logger.info("Attempting to delete roll ID: %d", roll_id)
            result = delete_roll(self.db, roll_id)
            if result:
                logger.debug("Successfully marked roll %d as removed", roll_id)
            else:
                logger.warning("Roll %d not found for deletion", roll_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Database error during deletion: %s", str(e))
            raise
        except Exception as e:
            logger.critical("Unexpected error in delete_roll: %s", str(e))
            raise

    def get_stats(self, start_date: datetime, end_date: datetime) -> RollStats:
        try:
            logger.info("Calculating stats from %s to %s",
                      start_date.isoformat(), end_date.isoformat())
            result = get_stats(self.db, start_date, end_date)
            logger.debug("Stats calculation completed. Total entries: %d", result["total_added"])
            return result
        except SQLAlchemyError as e:
            logger.error("Database error in get_stats: %s", str(e))
            raise
        except ValueError as e:
            logger.error("Invalid date format in get_stats: %s", str(e))
            raise
        except ZeroDivisionError as e:
            logger.error("Division by zero in stats calculation: %s", str(e))
            raise
        except Exception as e:
            logger.critical("Unexpected error in get_stats: %s", str(e))
            raise