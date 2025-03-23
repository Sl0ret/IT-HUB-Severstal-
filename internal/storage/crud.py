from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, Boolean
from datetime import datetime, UTC
from ..models.models import Roll
from ..models.schemas import RollCreate
from sqlalchemy import func
from ..logger.logger import logger
from typing import cast


def parse_range(range_str: str):
    try:
        if not range_str:
            return None
        parts = range_str.split(',')
        if len(parts) != 2:
            raise ValueError(f"Неверный формат диапазона: '{range_str}'")

        if '-' in parts[0]:
            return (
                datetime.strptime(parts[0], "%Y-%m-%d").replace(tzinfo=UTC),
                datetime.strptime(parts[1], "%Y-%m-%d").replace(tzinfo=UTC)
            )
        return (float(parts[0]), float(parts[1]))
    except Exception as e:
        logger.error("Ошибка парсинга диапазона: %s", str(e))
        raise


def apply_filters(query, filters: dict):
    valid_fields = {
        'id_range': Roll.id,
        'weight_range': Roll.weight,
        'length_range': Roll.length,
        'added_at_range': Roll.added_at,
        'removed_at_range': Roll.removed_at,
    }

    for field, value in filters.items():
        if field not in valid_fields or not value:
            continue

        min_val, max_val = parse_range(value)
        column = valid_fields[field]

        if field == 'removed_at_range':
            query = query.filter(
                and_(
                    or_(column >= min_val, column.is_(None)),
                    column <= max_val if max_val else True
                )
            )
        else:
            query = query.filter(and_(
                column >= min_val,
                column <= max_val if max_val else True
            ))
    return query


def get_rolls(db: Session, filters: dict = None):
    try:
        logger.info("Fetching rolls with filters: %s", filters)
        query = db.query(Roll)
        if filters:
            query = apply_filters(query, filters)
        result = query.all()
        logger.debug("Found %d rolls", len(result))
        return result
    except SQLAlchemyError as e:
        logger.error("Database error in get_rolls: %s", str(e))
        raise


def create_roll(db: Session, roll: RollCreate):
    try:
        logger.info("Creating roll: %s", roll.model_dump())
        new_roll = Roll(
            length=roll.length,
            weight=roll.weight,
            added_at=datetime.now(UTC)  # Setting timezone
        )
        db.add(new_roll)
        db.commit()
        return new_roll
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error: %s", e)
        raise


def delete_roll(db: Session, roll_id: int):
    try:
        roll = db.query(Roll).get(roll_id)
        if not roll:
            return None

        roll.removed_at = datetime.now(UTC)
        db.commit()
        return roll
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Deletion error: %s", e)
        raise


def get_roll_by_id(db: Session, roll_id: int) -> Roll | None:
    try:
        logger.debug("Attempting to fetch roll with ID: %d", roll_id)

        # Input data type validation
        if not isinstance(roll_id, int):
            logger.error("Invalid ID type: %s", type(roll_id).__name__)
            raise TypeError("Roll ID must be an integer")

        # Type-casted filter condition
        result = db.query(Roll).filter(
            cast(Roll.id == roll_id, Boolean)
        ).first()

        if not result:
            logger.warning("Roll with ID %d not found", roll_id)
        else:
            logger.debug("Successfully fetched roll ID: %d", roll_id)

        return result

    except SQLAlchemyError as e:
        logger.error("Database error: %s", str(e), exc_info=True)
        db.rollback()
        raise
    except (TypeError, ValueError) as e:
        logger.error("Validation error: %s", str(e))
        raise
    except Exception as e:
        logger.critical("Unexpected error: %s", str(e), exc_info=True)
        raise

def get_stats(db: Session, start_date: datetime, end_date: datetime):
    try:
        logger.info("Calculating stats from %s to %s",
                    start_date.isoformat(), end_date.isoformat())

        query = db.query(Roll).filter(
            and_(
                Roll.added_at <= end_date,
                (Roll.removed_at >= start_date) | (Roll.removed_at.is_(None))
            )
        )

        logger.debug("Executing total added query")
        total_added = query.filter(Roll.added_at.between(start_date, end_date)).count()

        logger.debug("Executing total removed query")
        total_removed = query.filter(Roll.removed_at.between(start_date, end_date)).count()

        logger.debug("Calculating aggregate stats")
        stats = db.query(
            func.avg(Roll.length).label('avg_length'),
            func.avg(Roll.weight).label('avg_weight'),
            func.max(Roll.length).label('max_length'),
            func.min(Roll.length).label('min_length'),
            func.max(Roll.weight).label('max_weight'),
            func.min(Roll.weight).label('min_weight'),
            func.sum(Roll.weight).label('total_weight')
        ).first()

        avg_length = stats.avg_length or 0
        avg_weight = stats.avg_weight or 0
        max_length = stats.max_length or 0
        min_length = stats.min_length or 0
        max_weight = stats.max_weight or 0
        min_weight = stats.min_weight or 0
        total_weight = stats.total_weight or 0

        logger.debug("Calculating time differences")
        time_diff_subq = db.query(
            func.julianday(Roll.removed_at) - func.julianday(Roll.added_at)
        ).filter(Roll.removed_at.is_not(None)).subquery()

        max_time_diff = db.query(func.max(time_diff_subq.c[0])).scalar() or 0
        min_time_diff = db.query(func.min(time_diff_subq.c[0])).scalar() or 0

        logger.debug("Calculating daily stats")
        daily_stats = db.query(
            func.date(Roll.added_at).label('date'),
            func.count(Roll.id).label('rolls_count'),
            func.sum(Roll.weight).label('total_weight')
        ).group_by(func.date(Roll.added_at)).all()

        min_rolls_day = min(daily_stats, key=lambda x: x.rolls_count, default=None)
        max_rolls_day = max(daily_stats, key=lambda x: x.rolls_count, default=None)
        min_weight_day = min(daily_stats, key=lambda x: x.total_weight, default=None)
        max_weight_day = max(daily_stats, key=lambda x: x.total_weight, default=None)

        logger.info("Stats calculation completed successfully")
        return {
            "total_added": total_added,
            "total_removed": total_removed,
            "avg_length": avg_length,
            "avg_weight": avg_weight,
            "max_length": max_length,
            "min_length": min_length,
            "max_weight": max_weight,
            "min_weight": min_weight,
            "total_weight": total_weight,
            "max_time_diff": max_time_diff,
            "min_time_diff": min_time_diff,
            "min_rolls_day": min_rolls_day.date if min_rolls_day else None,
            "max_rolls_day": max_rolls_day.date if max_rolls_day else None,
            "min_weight_day": min_weight_day.date if min_weight_day else None,
            "max_weight_day": max_weight_day.date if max_weight_day else None,
        }

    except SQLAlchemyError as e:
        logger.error("Database error in get_stats: %s", str(e))
        raise
    except ValueError as e:
        logger.error("Data processing error: %s", str(e))
        raise
    except Exception as e:
        logger.critical("Unexpected error in get_stats: %s", str(e))
        raise
