"""SQLite storage for tickets (Milestone 1: 'Store the ticket')."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tickets.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name  TEXT,
    email          TEXT,
    department     TEXT,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL,
    category       TEXT,
    category_conf  REAL,
    severity       TEXT,
    severity_conf  REAL,
    business_impact TEXT,
    priority       TEXT,
    status         TEXT DEFAULT 'Open',
    processing_ms  REAL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute(SCHEMA)


def format_id(row_id: int) -> str:
    return f"SP-T{1000 + row_id}"


def insert_ticket(data: dict) -> str:
    cols = ["employee_name", "email", "department", "title", "description", "category",
            "category_conf", "severity", "severity_conf", "business_impact", "priority",
            "status", "processing_ms"]
    with _conn() as conn:
        cur = conn.execute(
            f"INSERT INTO tickets ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [data.get(c) for c in cols],
        )
        return format_id(cur.lastrowid)


def _row_to_dict(row):
    d = dict(row)
    d["ticket_id"] = format_id(d["ticket_id"])
    return d


def list_tickets(limit: int = 20):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY ticket_id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_ticket(ticket_id: str):
    try:
        row_id = int(ticket_id.replace("SP-T", "")) - 1000
    except ValueError:
        return None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (row_id,)).fetchone()
    return _row_to_dict(row) if row else None


def stats():
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE date(created_at) = date('now')"
        ).fetchone()[0]
        avg_ms = conn.execute("SELECT AVG(processing_ms) FROM tickets").fetchone()[0]
        avg_conf = conn.execute("SELECT AVG(category_conf) FROM tickets").fetchone()[0]
        by_priority = {
            r[0]: r[1] for r in conn.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority")
        }
        by_category = {
            r[0]: r[1] for r in conn.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
        }
    return {
        "total": total,
        "today": today,
        "avg_processing_ms": round(avg_ms, 1) if avg_ms else None,
        "avg_category_confidence": round(avg_conf, 3) if avg_conf else None,
        "by_priority": by_priority,
        "by_category": by_category,
    }
