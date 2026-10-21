import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.getenv("PLAYGROUND_DB", os.path.join(os.path.dirname(__file__), "..", "playground.db"))


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                prompt TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                config TEXT NOT NULL,
                result TEXT NOT NULL
            )"""
        )


def save_run(prompt: str, system_prompt: str, config: dict, result: dict) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO runs (created_at, prompt, system_prompt, config, result) VALUES (?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), prompt, system_prompt, json.dumps(config), json.dumps(result)),
        )
        return cur.lastrowid


def list_runs(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_row(r) for r in rows]


def get_run(run_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return _row(row) if row else None


def delete_run(run_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        return cur.rowcount > 0


def clear_runs() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM runs")


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "created_at": r["created_at"],
        "prompt": r["prompt"],
        "system_prompt": r["system_prompt"],
        "config": json.loads(r["config"]),
        "result": {**json.loads(r["result"]), "id": r["id"]},
    }
