import sqlite3
import uuid
import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "tablekeeper.db"

app = FastAPI(
    title="TableKeeper Clean-Room Service",
    description="High-concurrency restaurant reservation engine with zero double-booking guarantee.",
    version="1.0.0"
)

@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=15000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                timezone TEXT NOT NULL DEFAULT 'America/Los_Angeles',
                address TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tables (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                table_number INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                location_zone TEXT NOT NULL DEFAULT 'main_dining',
                UNIQUE (restaurant_id, table_number)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL REFERENCES restaurants(id),
                table_id TEXT NOT NULL REFERENCES tables(id),
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                party_size INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('CONFIRMED', 'CANCELLED')),
                idempotency_key TEXT UNIQUE,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_res_table_times ON reservations (table_id, start_time, end_time, status);")
        
        # Seed default restaurants and tables
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute("""
            INSERT OR IGNORE INTO restaurants (id, name, timezone, address, created_at)
            VALUES 
                ('rest_luminary', 'Bistro Luminary', 'America/Los_Angeles', '452 Castro St, San Francisco, CA', ?),
                ('rest_elysian', 'Elysian Table', 'America/New_York', '180 Broadway, New York, NY', ?)
        """, (now_iso, now_iso))

        conn.execute("""
            INSERT OR IGNORE INTO tables (id, restaurant_id, table_number, capacity, location_zone)
            VALUES 
                ('tbl_lum_01', 'rest_luminary', 1, 2, 'indoor'),
                ('tbl_lum_02', 'rest_luminary', 2, 4, 'indoor'),
                ('tbl_lum_03', 'rest_luminary', 3, 6, 'patio'),
                ('tbl_ely_01', 'rest_elysian', 1, 2, 'indoor'),
                ('tbl_ely_02', 'rest_elysian', 2, 4, 'main_dining')
        """)

init_db()

# --- Pydantic Schemas ---
class ReservationRequest(BaseModel):
    restaurant_id: str
    table_id: str
    customer_name: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=3)
    party_size: int = Field(..., gt=0)
    start_time: str # ISO 8601 UTC (e.g., 2026-10-05T19:00:00Z)
    end_time: str   # ISO 8601 UTC (e.g., 2026-10-05T20:30:00Z)
    idempotency_key: Optional[str] = None

class ReservationResponse(BaseModel):
    id: str
    restaurant_id: str
    table_id: str
    customer_name: str
    customer_email: str
    party_size: int
    start_time: str
    end_time: str
    status: str
    is_replayed: bool = False

# --- Helper Functions ---
def parse_iso(dt_str: str) -> datetime.datetime:
    try:
        # Standardize ISO parse
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        dt = datetime.datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO 8601 datetime format: {dt_str}"
        )

# --- Routes ---
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TableKeeper", "version": "1.0.0"}

@app.get("/api/restaurants")
def get_restaurants():
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, name, timezone, address FROM restaurants").fetchall()
        return [
            {"id": r[0], "name": r[1], "timezone": r[2], "address": r[3]}
            for r in rows
        ]

@app.get("/api/tables")
def get_tables(restaurant_id: str = Query(...)):
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            "SELECT id, restaurant_id, table_number, capacity, location_zone FROM tables WHERE restaurant_id = ? ORDER BY table_number",
            (restaurant_id,)
        ).fetchall()
        return [
            {"id": r[0], "restaurant_id": r[1], "table_number": r[2], "capacity": r[3], "location_zone": r[4]}
            for r in rows
        ]

@app.get("/api/reservations")
def get_reservations(restaurant_id: str = Query(...), date: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if date:
            rows = cursor.execute("""
                SELECT id, restaurant_id, table_id, customer_name, customer_email, party_size, start_time, end_time, status, created_at
                FROM reservations
                WHERE restaurant_id = ? AND start_time LIKE ? AND status = 'CONFIRMED'
                ORDER BY start_time ASC
            """, (restaurant_id, f"{date}%")).fetchall()
        else:
            rows = cursor.execute("""
                SELECT id, restaurant_id, table_id, customer_name, customer_email, party_size, start_time, end_time, status, created_at
                FROM reservations
                WHERE restaurant_id = ? AND status = 'CONFIRMED'
                ORDER BY start_time ASC
            """, (restaurant_id,)).fetchall()
        
        return [
            {
                "id": r[0], "restaurant_id": r[1], "table_id": r[2], "customer_name": r[3],
                "customer_email": r[4], "party_size": r[5], "start_time": r[6], "end_time": r[7],
                "status": r[8], "created_at": r[9]
            }
            for r in rows
        ]

@app.post("/api/reservations", status_code=status.HTTP_201_CREATED, response_model=ReservationResponse)
def create_reservation(req: ReservationRequest):
    # Validate datetime order
    start_dt = parse_iso(req.start_time)
    end_dt = parse_iso(req.end_time)
    if end_dt <= start_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    if (end_dt - start_dt).total_seconds() > 14400: # 4 hour max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation duration cannot exceed 4 hours"
        )

    # Standardize format for storage (ISO 8601 UTC)
    iso_start = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    iso_end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    with get_db() as conn:
        # Atomic lock: BEGIN IMMEDIATE prevents any other writer from entering
        conn.execute("BEGIN IMMEDIATE;")
        try:
            # 1. Idempotency Check
            if req.idempotency_key:
                existing = conn.execute("""
                    SELECT id, restaurant_id, table_id, customer_name, customer_email, party_size, start_time, end_time, status
                    FROM reservations
                    WHERE idempotency_key = ?
                """, (req.idempotency_key,)).fetchone()

                if existing:
                    conn.execute("COMMIT;")
                    return ReservationResponse(
                        id=existing[0],
                        restaurant_id=existing[1],
                        table_id=existing[2],
                        customer_name=existing[3],
                        customer_email=existing[4],
                        party_size=existing[5],
                        start_time=existing[6],
                        end_time=existing[7],
                        status=existing[8],
                        is_replayed=True
                    )

            # 2. Verify restaurant and table existence
            table_row = conn.execute(
                "SELECT capacity, restaurant_id FROM tables WHERE id = ?",
                (req.table_id,)
            ).fetchone()
            if not table_row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
            
            capacity, rest_id = table_row
            if rest_id != req.restaurant_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table does not belong to specified restaurant")

            # 3. Capacity Check
            if req.party_size > capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Party size ({req.party_size}) exceeds table capacity ({capacity})"
                )

            # 4. Overlap Check (The Core Concurrency Defense)
            # Overlap exists if NOT (new_start >= existing_end OR new_end <= existing_start)
            conflict = conn.execute("""
                SELECT id, start_time, end_time
                FROM reservations
                WHERE table_id = ?
                  AND status = 'CONFIRMED'
                  AND NOT (end_time <= ? OR start_time >= ?)
            """, (req.table_id, iso_start, iso_end)).fetchone()

            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Table slot is already booked from {conflict[1]} to {conflict[2]}"
                )

            # 5. Insert Confirmed Reservation
            res_id = f"res_{uuid.uuid4().hex[:10]}"
            now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            conn.execute("""
                INSERT INTO reservations (
                    id, restaurant_id, table_id, customer_name, customer_email,
                    party_size, start_time, end_time, status, idempotency_key, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?, ?)
            """, (
                res_id, req.restaurant_id, req.table_id, req.customer_name,
                req.customer_email, req.party_size, iso_start, iso_end,
                req.idempotency_key, now_iso
            ))

            conn.execute("COMMIT;")
            return ReservationResponse(
                id=res_id,
                restaurant_id=req.restaurant_id,
                table_id=req.table_id,
                customer_name=req.customer_name,
                customer_email=req.customer_email,
                party_size=req.party_size,
                start_time=iso_start,
                end_time=iso_end,
                status="CONFIRMED",
                is_replayed=False
            )

        except HTTPException:
            conn.execute("ROLLBACK;")
            raise
        except Exception as e:
            conn.execute("ROLLBACK;")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database execution error: {str(e)}"
            )

@app.delete("/api/reservations/{res_id}")
def cancel_reservation(res_id: str):
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE;")
        try:
            row = conn.execute("SELECT id, status FROM reservations WHERE id = ?", (res_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Reservation not found")
            if row[1] == "CANCELLED":
                conn.execute("COMMIT;")
                return {"id": res_id, "status": "ALREADY_CANCELLED"}
            
            conn.execute("UPDATE reservations SET status = 'CANCELLED' WHERE id = ?", (res_id,))
            conn.execute("COMMIT;")
            return {"id": res_id, "status": "CANCELLED"}
        except HTTPException:
            conn.execute("ROLLBACK;")
            raise
        except Exception as e:
            conn.execute("ROLLBACK;")
            raise HTTPException(status_code=500, detail=str(e))

# --- Static Frontend Mount ---
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_portal():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>TableKeeper Service Running (Static UI not built)</h1>")
