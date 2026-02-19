"""Local SQLite storage for Hevy data (user + workouts) for fast loads after first fetch."""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd


def _db_path() -> str:
    """Path to the SQLite database file in the project directory."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "hevy_data.db")


def _api_key_hash(api_key: str) -> str:
    """Hash API key for storage (never store the key itself)."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def save(api_key: str, data: Dict[str, Any]) -> None:
    """
    Save user and workouts to local SQLite. Overwrites existing row for this API key.
    """
    try:
        user = data.get("user", {})
        workouts = data.get("workouts_raw", {}).get("workouts", data.get("workouts", []))
        user_json = json.dumps(user)
        workouts_json = json.dumps(workouts)
        updated_at = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(_db_path())
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                api_key_hash TEXT PRIMARY KEY,
                user_json TEXT NOT NULL,
                workouts_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO cache (api_key_hash, user_json, workouts_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(api_key_hash) DO UPDATE SET
                user_json = excluded.user_json,
                workouts_json = excluded.workouts_json,
                updated_at = excluded.updated_at
            """,
            (_api_key_hash(api_key), user_json, workouts_json, updated_at),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Fall back to API-only; app still works


def load(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Load user and workouts from local SQLite. Rebuilds workouts_raw and workouts_df.
    Returns None if no data or on error.
    """
    try:
        conn = sqlite3.connect(_db_path(), timeout=5)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT user_json, workouts_json FROM cache WHERE api_key_hash = ?",
            (_api_key_hash(api_key),),
        ).fetchone()
        conn.close()

        if row is None:
            return None

        user = json.loads(row["user_json"])
        workouts = json.loads(row["workouts_json"])

        workouts_raw = {"workouts": workouts}
        workouts_df = pd.json_normalize(workouts) if workouts else pd.DataFrame()

        return {
            "user": user,
            "workouts_raw": workouts_raw,
            "workouts": workouts,
            "workouts_df": workouts_df,
        }
    except Exception:
        return None


def clear(api_key: str) -> None:
    """Delete cached data for this API key."""
    try:
        conn = sqlite3.connect(_db_path())
        conn.execute("DELETE FROM cache WHERE api_key_hash = ?", (_api_key_hash(api_key),))
        conn.commit()
        conn.close()
    except Exception:
        pass
