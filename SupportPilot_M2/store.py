"""Agent feedback storage. Resolution Rate = helpful / total feedback (so it is measured, not hard-coded)."""
import sqlite3

import config


def _conn():
    conn = sqlite3.connect(config.FEEDBACK_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS feedback ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT, helpful INTEGER, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    return conn


def add_feedback(ticket_id: str, helpful: bool):
    with _conn() as conn:
        conn.execute("INSERT INTO feedback (ticket_id, helpful) VALUES (?, ?)", (ticket_id, int(helpful)))


def resolution_stats():
    with _conn() as conn:
        total, helpful = conn.execute("SELECT COUNT(*), COALESCE(SUM(helpful), 0) FROM feedback").fetchone()
    return {"feedback_count": total, "resolution_rate": round(helpful / total, 3) if total else None}
