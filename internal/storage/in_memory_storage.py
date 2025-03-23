from datetime import datetime, UTC
from typing import List, Dict, Optional
from ..models.schemas import RollStats, RollCreate, RollResponse
from .storage import StorageInterface
from ..logger.logger import logger


class InMemoryStorage(StorageInterface):
    def __init__(self):
        self.rolls = []
        self._next_id = 1
        logger.info("InMemoryStorage initialized with empty storage")

    def create_roll(self, roll: RollCreate) -> RollResponse:
        try:
            roll_data = RollResponse(
                id=self._next_id,
                length=roll.length,
                weight=roll.weight,
                added_at=datetime.now(UTC),
                removed_at=None
            )
            self.rolls.append(roll_data)
            logger.debug("Created in-memory roll ID: %d", self._next_id)
            self._next_id += 1
            return roll_data
        except Exception as e:
            logger.error("Failed to create in-memory roll: %s", str(e))
            raise

    def get_rolls(self, filters: Dict[str, Optional[str]]) -> List[RollResponse]:
        try:
            logger.debug("Applying filters: %s", filters)
            filtered = self.rolls.copy()

            if filters.get("id_range"):
                try:
                    id_min, id_max = map(int, filters["id_range"].split(","))
                    filtered = [r for r in filtered if id_min <= r.id <= id_max]
                    logger.debug("Applied ID filter: %d-%d", id_min, id_max)
                except ValueError as e:
                    logger.error("Invalid ID range format: %s", str(e))
                    raise

            if filters.get("weight_range"):
                try:
                    weight_min, weight_max = map(float, filters["weight_range"].split(","))
                    filtered = [r for r in filtered if weight_min <= r.weight <= weight_max]
                    logger.debug("Applied weight filter: %.2f-%.2f", weight_min, weight_max)
                except ValueError as e:
                    logger.error("Invalid weight range format: %s", str(e))
                    raise

            if filters.get("length_range"):
                try:
                    length_min, length_max = map(float, filters["length_range"].split(","))
                    filtered = [r for r in filtered if length_min <= r.length <= length_max]
                    logger.debug("Applied length filter: %.2f-%.2f", length_min, length_max)
                except ValueError as e:
                    logger.error("Invalid length range format: %s", str(e))
                    raise

            if filters.get("added_at_range"):
                try:
                    added_min, added_max = map(datetime.fromisoformat, filters["added_at_range"].split(","))
                    filtered = [r for r in filtered if added_min <= r.added_at <= added_max]
                    logger.debug("Applied added_at filter: %s - %s", added_min, added_max)
                except ValueError as e:
                    logger.error("Invalid added_at range format: %s", str(e))
                    raise

            if filters.get("removed_at_range"):
                try:
                    removed_min, removed_max = map(datetime.fromisoformat, filters["removed_at_range"].split(","))
                    filtered = [r for r in filtered if r.removed_at and removed_min <= r.removed_at <= removed_max]
                    logger.debug("Applied removed_at filter: %s - %s", removed_min, removed_max)
                except ValueError as e:
                    logger.error("Invalid removed_at range format: %s", str(e))
                    raise

            logger.info("Returning %d filtered rolls", len(filtered))
            return filtered
        except Exception as e:
            logger.error("Failed to filter rolls: %s", str(e))
            raise

    def delete_roll(self, roll_id: int) -> Optional[RollResponse]:
        try:
            logger.debug("Attempting to delete roll ID: %d", roll_id)
            for index, roll in enumerate(self.rolls):
                if roll.id == roll_id:
                    self.rolls[index] = roll.copy(update={"removed_at": datetime.now(UTC)})
                    logger.info("Marked roll %d as removed", roll_id)
                    return self.rolls[index]
            logger.warning("Roll %d not found for deletion", roll_id)
            return None
        except Exception as e:
            logger.error("Failed to delete roll %d: %s", roll_id, str(e))
            raise

    def get_stats(self, start_date: datetime, end_date: datetime) -> RollStats:
        try:
            logger.info("Calculating stats between %s and %s",
                        start_date.isoformat(), end_date.isoformat())

            filtered = [r for r in self.rolls if start_date <= r.added_at <= end_date]
            total_added = len(filtered)
            total_removed = len([r for r in filtered if r.removed_at])

            lengths = [r.length for r in filtered]
            weights = [r.weight for r in filtered]
            time_diffs = [(r.removed_at - r.added_at).days for r in filtered if r.removed_at]

            logger.debug("Processed %d entries for stats", len(filtered))

            return RollStats(
                total_added=total_added,
                total_removed=total_removed,
                avg_length=sum(lengths) / len(lengths) if lengths else 0,
                avg_weight=sum(weights) / len(weights) if weights else 0,
                max_length=max(lengths) if lengths else 0,
                min_length=min(lengths) if lengths else 0,
                max_weight=max(weights) if weights else 0,
                min_weight=min(weights) if weights else 0,
                total_weight=sum(weights) if weights else 0,
                max_time_diff=max(time_diffs) if time_diffs else None,
                min_time_diff=min(time_diffs) if time_diffs else None
            )
        except ZeroDivisionError:
            logger.error("Empty dataset for stats calculation")
            return RollStats(
                total_added=0,
                total_removed=0,
                avg_length=0,
                avg_weight=0,
                max_length=0,
                min_length=0,
                max_weight=0,
                min_weight=0,
                total_weight=0,
                max_time_diff=None,
                min_time_diff=None
            )
        except Exception as e:
            logger.critical("Failed to calculate stats: %s", str(e))
            raise