# Stage 2: TableKeeper Dynamic Availability Service

> **Track:** `tablekeeper` (Restaurant Reservation Platform)  
> **Evolutionary Feature:** Real-Time Dynamic Slot Finder & Capacity Partitioning  
> **Core Guarantee:** Zero double-booking under concurrency, network retries, and time zones.  

---

## ⚡ What's New in Stage 2

1. **Dynamic Slot Finder Endpoint (`GET /api/slots/available`):**
   * Calculates open slots across all restaurant tables in real time.
   * Partitions by party size and operating hours (17:00 – 21:00 UTC).
   * Automatically omits tables with overlapping confirmed bookings.
2. **Two-Pointer / Interval Pre-Filter:**
   * Rapid in-memory evaluation of booked time windows.
   * Sub-millisecond response time for availability searches.
3. **Preserved Backwards Compatibility:**
   * All Stage 1 endpoints, concurrency invariants, and atomic transaction locks (`BEGIN IMMEDIATE;`) remain 100% functional.

---

## 🚀 Quick Start (Isolated Environment)

```bash
# One-click execution in isolated .venv
./run.sh

# Or standard make
make setup
make run
```

---

## 🧪 Automated Testing

```bash
# Run full Stage 2 test suite including dynamic slot availability checks
make test

# Run offline container isolation verification
./run_offline_test.sh
```
