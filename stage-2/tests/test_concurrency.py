import pytest
import concurrent.futures
from fastapi.testclient import TestClient
from src.main import app, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clear reservations table before each test run
    with get_db() as conn:
        conn.execute("DELETE FROM reservations;")
    yield

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_restaurant_and_table_listings():
    resp = client.get("/api/restaurants")
    assert resp.status_code == 200
    restaurants = resp.json()
    assert len(restaurants) >= 2
    rest_id = restaurants[0]["id"]

    resp = client.get(f"/api/tables?restaurant_id={rest_id}")
    assert resp.status_code == 200
    tables = resp.json()
    assert len(tables) >= 2

def test_successful_reservation():
    payload = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_01",
        "customer_name": "Marcus Vance",
        "customer_email": "marcus@test.com",
        "party_size": 2,
        "start_time": "2026-10-05T19:00:00Z",
        "end_time": "2026-10-05T20:30:00Z",
        "idempotency_key": "idemp_test_001"
    }
    resp = client.post("/api/reservations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "CONFIRMED"
    assert data["is_replayed"] is False
    assert data["party_size"] == 2

def test_capacity_exceeded_rejected():
    # tbl_lum_01 has capacity 2; request party size 5
    payload = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_01",
        "customer_name": "Big Party",
        "customer_email": "party@test.com",
        "party_size": 5,
        "start_time": "2026-10-05T19:00:00Z",
        "end_time": "2026-10-05T20:30:00Z"
    }
    resp = client.post("/api/reservations", json=payload)
    assert resp.status_code == 400
    assert "exceeds table capacity" in resp.json()["detail"]

def test_invalid_time_range_rejected():
    payload = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_01",
        "customer_name": "Invalid Time",
        "customer_email": "invalid@test.com",
        "party_size": 2,
        "start_time": "2026-10-05T20:00:00Z",
        "end_time": "2026-10-05T19:00:00Z" # end before start!
    }
    resp = client.post("/api/reservations", json=payload)
    assert resp.status_code == 400

def test_idempotency_key_replay():
    payload = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_02",
        "customer_name": "Idempotent Guest",
        "customer_email": "idemp@test.com",
        "party_size": 3,
        "start_time": "2026-10-06T18:00:00Z",
        "end_time": "2026-10-06T19:30:00Z",
        "idempotency_key": "unique_key_replay_test"
    }
    # Initial request
    resp1 = client.post("/api/reservations", json=payload)
    assert resp1.status_code == 201
    booking_id = resp1.json()["id"]

    # Replay identical request
    resp2 = client.post("/api/reservations", json=payload)
    assert resp2.status_code == 201 # Or 200
    data2 = resp2.json()
    assert data2["id"] == booking_id
    assert data2["is_replayed"] is True

def test_adjacent_time_slots_allowed():
    """Verify slots immediately adjacent to each other do not conflict."""
    # Slot 1: 18:00 to 19:00
    p1 = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_01",
        "customer_name": "Early Diner",
        "customer_email": "early@test.com",
        "party_size": 2,
        "start_time": "2026-10-07T18:00:00Z",
        "end_time": "2026-10-07T19:00:00Z"
    }
    # Slot 2: 19:00 to 20:00 (Starts right when slot 1 ends)
    p2 = {
        "restaurant_id": "rest_luminary",
        "table_id": "tbl_lum_01",
        "customer_name": "Late Diner",
        "customer_email": "late@test.com",
        "party_size": 2,
        "start_time": "2026-10-07T19:00:00Z",
        "end_time": "2026-10-07T20:00:00Z"
    }
    r1 = client.post("/api/reservations", json=p1)
    r2 = client.post("/api/reservations", json=p2)
    assert r1.status_code == 201
    assert r2.status_code == 201

def test_concurrency_zero_double_booking():
    """
    CORE INVARIANT STRESS TEST:
    25 parallel client threads compete simultaneously to book the exact same table slot.
    INVARIANT: Exactly ONE succeeds (HTTP 201). Exactly 24 receive HTTP 409 Conflict.
    Zero double-bookings are permitted.
    """
    start_time = "2026-10-08T19:30:00Z"
    end_time = "2026-10-08T21:00:00Z"
    table_id = "tbl_lum_03"
    rest_id = "rest_luminary"

    def attempt_booking(worker_idx):
        payload = {
            "restaurant_id": rest_id,
            "table_id": table_id,
            "customer_name": f"Concurrent Competitor #{worker_idx}",
            "customer_email": f"competitor{worker_idx}@concurrency.org",
            "party_size": 4,
            "start_time": start_time,
            "end_time": end_time,
            "idempotency_key": f"key_concurrency_race_{worker_idx}"
        }
        # Use fresh connection client
        c = TestClient(app)
        return c.post("/api/reservations", json=payload)

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(25)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r.status_code == 201]
    conflicts = [r for r in results if r.status_code == 409]

    # Strict invariant validation
    assert len(successes) == 1, f"INVARIANT VIOLATION: Expected 1 booking, got {len(successes)}"
    assert len(conflicts) == 24, f"INVARIANT VIOLATION: Expected 24 conflicts, got {len(conflicts)}"

def test_dynamic_slots_available():
    """Stage 2 Test: Dynamic availability computation returns available slots and excludes booked ones."""
    date = "2026-10-15"
    rest_id = "rest_luminary"
    
    # Check initial availability for party size 2
    resp = client.get(f"/api/slots/available?restaurant_id={rest_id}&party_size=2&date={date}")
    assert resp.status_code == 200
    initial_slots = resp.json()
    assert len(initial_slots) > 0

    # Book a specific table at 19:00
    target_slot = [s for s in initial_slots if "19:00" in s["start_time"]][0]
    p = {
        "restaurant_id": rest_id,
        "table_id": target_slot["table_id"],
        "customer_name": "Availability Blocker",
        "customer_email": "blocker@test.com",
        "party_size": 2,
        "start_time": target_slot["start_time"],
        "end_time": target_slot["end_time"],
        "idempotency_key": "avail_block_key"
    }
    b_resp = client.post("/api/reservations", json=p)
    assert b_resp.status_code == 201

    # Re-query availability: target table slot should now be missing from available slots
    resp2 = client.get(f"/api/slots/available?restaurant_id={rest_id}&party_size=2&date={date}")
    assert resp2.status_code == 200
    updated_slots = resp2.json()
    
    # Assert target table slot is no longer returned
    conflicting = [s for s in updated_slots if s["table_id"] == target_slot["table_id"] and s["start_time"] == target_slot["start_time"]]
    assert len(conflicting) == 0
