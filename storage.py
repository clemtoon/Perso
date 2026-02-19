"""Storage for Hevy data (user + workouts). Uses Supabase."""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

# Optional Supabase
try:
    from supabase import create_client
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False

def _api_key_hash(api_key: str) -> str:
    """Hash API key for storage (never store the key itself)."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def _use_supabase() -> bool:
    """Use Supabase if URL and key are set."""
    return (
        _SUPABASE_AVAILABLE
        and os.environ.get("SUPABASE_URL")
        and os.environ.get("SUPABASE_KEY")
    )


def _get_supabase_client():
    """Lazy-init Supabase client."""
    from supabase import create_client
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"],
    )


def save(api_key: str, data: Dict[str, Any]) -> None:
    """Save user and workouts to Supabase."""
    user = data.get("user", {})
    workouts = data.get("workouts_raw", {}).get("workouts", data.get("workouts", []))
    user_json = json.dumps(user)
    workouts_json = json.dumps(workouts)
    updated_at = datetime.now(timezone.utc).isoformat()
    key_hash = _api_key_hash(api_key)
    row = {
        "api_key_hash": key_hash,
        "user_json": user_json,
        "workouts_json": workouts_json,
        "updated_at": updated_at,
    }

    if _use_supabase():
        try:
            client = _get_supabase_client()
            client.table("hevy_cache").upsert(row, on_conflict="api_key_hash").execute()
        except Exception:
            pass


def load(api_key: str) -> Optional[Dict[str, Any]]:
    """Load user and workouts. Returns None if no data or on error."""
    key_hash = _api_key_hash(api_key)

    if _use_supabase():
        try:
            client = _get_supabase_client()
            resp = (
                client.table("hevy_cache")
                .select("user_json, workouts_json")
                .eq("api_key_hash", key_hash)
                .maybe_single()
                .execute()
            )
            if not resp.data:
                return None
            row = resp.data
        except Exception:
            return None
    else:
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


def clear(api_key: str) -> None:
    """Delete cached data for this API key."""
    key_hash = _api_key_hash(api_key)

    if _use_supabase():
        try:
            client = _get_supabase_client()
            client.table("hevy_cache").delete().eq("api_key_hash", key_hash).execute()
        except Exception:
            pass
