# Stage 1: TableKeeper Clean-Room Service

> **Track:** `tablekeeper` (Restaurant Reservation Platform)  
> **Core Guarantee:** Zero double-booking under concurrency, network retries, and time zones.  
> **Engine:** FastAPI + SQLite (WAL Mode, `BEGIN IMMEDIATE;` atomic locking).  

---

## ⚡ Architecture & Concurrency Defense

1. **Atomic Transaction Locking (`BEGIN IMMEDIATE;`):** Prevents TOCTOU race conditions by locking SQLite in exclusive write mode before checking availability.
2. **Interval Overlap Arithmetic:** Strictly evaluates `NOT (existing_end <= new_start OR existing_start >= new_end)` to prevent any overlap on confirmed reservations for the same table.
3. **Idempotency Journaling:** Unique `idempotency_key` ensures retried network requests replay the exact original reservation without duplicating bookings.
4. **Time Zone Normalization:** All reservations are stored in standardized ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`), with restaurant IANA time zone support.

---

## 🚀 Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run service
uvicorn src.main:app --host 0.0.0.0 --port 8080
```
Open `http://localhost:8080/` in your browser to interact with the responsive reservation portal.

---

## 🧪 Automated Testing

### Run Functional & Concurrency Race Stress Tests:
```bash
pytest tests/test_concurrency.py -v
```
*Includes a 25-thread parallel stress test verifying that only 1 booking succeeds and 24 receive HTTP 409 Conflict.*

### Run Offline Container Verification (`--network none`):
```bash
./run_offline_test.sh
```

---

## 📋 REST API Contracts

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `GET` | `/api/restaurants` | List supported restaurants and their timezones |
| `GET` | `/api/tables?restaurant_id={id}` | List restaurant tables with seat capacity |
| `GET` | `/api/reservations?restaurant_id={id}` | List confirmed bookings |
| `POST` | `/api/reservations` | Create reservation (atomic, idempotency-protected) |
| `DELETE` | `/api/reservations/{id}` | Cancel reservation and release slot |
