import pytest
from fastapi import status
from datetime import datetime, timedelta
from internal.models import schemas


def test_create_roll(client):
    response = client.post(
        "/rolls/",
        json={"length": 10.5, "weight": 100.0}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "id" in response.json()
    assert response.json()["removed_at"] is None

    response = client.post(
        "/rolls/",
        json={"length": -5, "weight": "invalid"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_rolls(client):
    rolls = [
        {"length": 10.0, "weight": 100.0},
        {"length": 20.0, "weight": 200.0},
        {"length": 30.0, "weight": 300.0}
    ]
    for roll in rolls:
        client.post("/rolls/", json=roll)

    test_cases = [
        ("length_range=15,25", 1),
        ("weight_range=150,250", 1),
        ("id_range=2,2", 1),
        ("removed_at_range=2099-01-01,2100-01-01", 0),
        ("invalid_filter=test", 3)
    ]

    for filter_query, expected_count in test_cases:
        response = client.get(f"/rolls/?{filter_query}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == expected_count

    response = client.get("/rolls/?length_range=invalid")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_roll(client):
    create_response = client.post("/rolls/", json={"length": 10.5, "weight": 100.0})
    roll_id = create_response.json()["id"]

    delete_response = client.delete(f"/rolls/{roll_id}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["removed_at"] is not None

    second_delete_response = client.delete(f"/rolls/{roll_id}")
    assert second_delete_response.status_code == status.HTTP_404_NOT_FOUND

    response = client.delete("/rolls/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_stats(client):
    now = datetime.utcnow()
    test_data = [
        {"length": 10, "weight": 100, "added_at": now - timedelta(days=2)},
        {"length": 20, "weight": 200, "added_at": now - timedelta(days=1)},
        {"length": 30, "weight": 300, "added_at": now}
    ]

    for data in test_data:
        client.post("/rolls/", json=data)

    delete_response = client.delete("/rolls/1")

    start = (now - timedelta(days=3)).isoformat()
    end = (now + timedelta(days=1)).isoformat()

    response = client.get(f"/rolls/stats/?start_date={start}&end_date={end}")
    assert response.status_code == status.HTTP_200_OK

    stats = response.json()
    assert stats["total_added"] == 3
    assert stats["total_removed"] == 1
    assert stats["avg_length"] == 20.0
    assert stats["max_weight"] == 300.0

    response = client.get("/rolls/stats/?start_date=invalid&end_date=format")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    far_future = (now + timedelta(days=365)).isoformat()
    response = client.get(f"/rolls/stats/?start_date={far_future}&end_date={far_future}")
    assert response.json()["total_added"] == 0