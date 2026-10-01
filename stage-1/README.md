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

## 🚀 Quick Start (Isolated Environment & One-Click Execution)

To guarantee zero pollution of your system Python environment (and prevent PEP 668 errors on macOS / Linux), choose from these standard options:

### Option 1: One-Click Automated Launcher (Recommended)
Automatically creates an isolated `.venv`, syncs dependencies, and boots the service:
```bash
./run.sh
```

### Option 2: Standard Makefile Workflow
```bash
# Setup isolated .venv and install dependencies
make setup

# Launch the service on http://localhost:8080
make run

# Run concurrency test suite inside .venv
make test
```

### Option 3: Zero-Dependency Docker Run
No Python or pip needed on the host machine:
```bash
make docker-build
make docker-run
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
