# Stage 3: TableKeeper Global Timezone & Waitlist Auto-Promotion

> **Track:** `tablekeeper` (Restaurant Reservation Platform)  
> **Evolutionary Feature:** Cross-Timezone Operations & Atomic Waitlist Auto-Promotion  
> **Core Guarantee:** Zero double-booking under concurrency, network retries, and time zones.  

---

## ⚡ What's New in Stage 3

1. **Global Multi-Timezone Architecture:**
   * Full IANA timezone mapping across 4 global dining destinations:
     * San Francisco (`America/Los_Angeles`)
     * New York (`America/New_York`)
     * London (`Europe/London`)
     * Tokyo (`Asia/Tokyo`)
   * Normalized storage in ISO 8601 UTC with offset transparency.
2. **Atomic Waitlist Auto-Promotion:**
   * When a guest cancels a booking (`DELETE /api/reservations/{id}`), the engine atomically queries the waitlist.
   * If a matching guest is found, the slot is **automatically promoted** to a confirmed booking in the same atomic transaction, ensuring zero slot leakage and zero race conditions.
3. **Full Backwards Compatibility:**
   * 100% compatibility with Stage 1 and Stage 2 contract suites.

---

## 🚀 Quick Start & Testing

```bash
# Launch in isolated environment
./run.sh

# Run Stage 3 test suite
make test

# Verify offline container build
./run_offline_test.sh
```
