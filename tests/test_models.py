from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from internal.models.models import Roll


def test_roll_creation_with_valid_data(db_session: Session):
    test_data = {
        "length": 15.5,
        "weight": 300.0,
    }

    roll = Roll(**test_data)
    db_session.add(roll)
    db_session.commit()

    assert roll.id is not None
    assert isinstance(roll.added_at, datetime)
    assert roll.removed_at is None
    assert roll.length == test_data["length"]
    assert roll.weight == test_data["weight"]


def test_roll_default_values(db_session: Session):
    roll = Roll(length=10.0, weight=100.0)
    db_session.add(roll)
    db_session.commit()

    assert roll.added_at is not None
    assert roll.removed_at is None


def test_roll_null_constraints(db_session: Session):
    with pytest.raises(IntegrityError):
        roll = Roll(length=None, weight=None)
        db_session.add(roll)
        db_session.commit()
        db_session.flush()


def test_roll_negative_values(db_session: Session):
    with pytest.raises(IntegrityError):
        roll = Roll(length=-5.0, weight=-100.0)
        db_session.add(roll)
        db_session.commit()
        db_session.flush()


def test_roll_update_operation(db_session: Session):
    original_length = 10.0
    roll = Roll(length=original_length, weight=100.0)
    db_session.add(roll)
    db_session.commit()

    new_length = 20.0
    roll.length = new_length
    db_session.commit()

    updated_roll = db_session.get(Roll, roll.id)
    assert updated_roll.length == new_length


def test_roll_soft_delete(db_session: Session):
    roll = Roll(length=10.0, weight=100.0)
    db_session.add(roll)
    db_session.commit()

    delete_time = datetime.now(timezone.utc)
    roll.removed_at = delete_time
    db_session.commit()

    updated_roll = db_session.get(Roll, roll.id)
    assert updated_roll.removed_at == delete_time


def test_roll_string_representation():
    test_id = 1
    test_length = 10.0
    test_weight = 100.0

    roll = Roll(id=test_id, length=test_length, weight=test_weight)

    expected_repr = f"<Roll(id={test_id}, length={test_length}, weight={test_weight})>"
    assert str(roll) == expected_repr
    assert repr(roll) == expected_repr