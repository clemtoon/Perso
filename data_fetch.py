"""Hevy API fetch: user info and workouts; caching and progress callback."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from hevy_client import (
    HevyApiError,
    get_api_key as get_env_api_key,
    get_user_info,
    get_workouts,
    get_workout_by_id,
    get_workouts_count,
)

from workout_parsing import extract_items, first_present


def resolve_api_key() -> Optional[str]:
    """Resolve the API key from environment or .env file."""
    return get_env_api_key()


WORKOUTS_PER_PAGE = 50
MAX_WORKOUT_PAGES = 500  # safety cap (~25k workouts)
MAX_ENRICH_WORKOUTS = 100  # cap how many get_workout_by_id calls; None = no cap
ENRICH_MAX_WORKERS = 2  # parallel enrichment (2–4 safe for Hevy API; 1 = sequential)


def _fetch_user_and_workouts_impl(
    api_key: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    Fetch user info and all workouts. Optional progress_callback(progress_0_to_1, message).
    """
    def report(p: float, msg: str) -> None:
        if progress_callback is not None:
            progress_callback(p, msg)

    report(0.0, "Fetching user info…")
    user = get_user_info(api_key)

    # Use /v1/workouts/count if available for accurate progress (see api.hevyapp.com/docs)
    total_count = get_workouts_count(api_key) if api_key else None
    if total_count is not None and total_count > 0:
        total_pages = max(1, min((total_count + WORKOUTS_PER_PAGE - 1) // WORKOUTS_PER_PAGE, MAX_WORKOUT_PAGES))
    else:
        total_pages = 1

    report(0.05, "Fetching workout list…")
    first = get_workouts(api_key=api_key, page=1, limit=WORKOUTS_PER_PAGE)
    all_workouts = first.get("workouts", []) or extract_items(first)
    page_count = first.get("page_count")
    if page_count is not None:
        try:
            page_count = int(page_count)
        except (TypeError, ValueError):
            page_count = None
    if total_pages == 1 and page_count is not None:
        total_pages = page_count
    for page in range(2, MAX_WORKOUT_PAGES + 1):
        resp = get_workouts(api_key=api_key, page=page, limit=WORKOUTS_PER_PAGE)
        more = resp.get("workouts", []) or extract_items(resp)
        all_workouts.extend(more)
        p = min(0.40, 0.05 + 0.35 * (page / max(1, total_pages)))
        report(p, f"Fetching workout list… (page {page})")
        got_short_page = len(more) < WORKOUTS_PER_PAGE
        if got_short_page and (page_count is None or page >= page_count):
            break

    report(0.40, "Loading workout details…")

    def _workout_has_set_data(w: Dict[str, Any]) -> bool:
        for ex in w.get("exercises") or []:
            for s in ex.get("sets") or []:
                if not isinstance(s, dict):
                    continue
                reps = first_present(s, ("reps", "repCount"))
                weight = first_present(s, ("weight_kg", "weightKg", "weight", "load"))
                if reps is not None or weight is not None:
                    return True
        return False

    def _fetch_one_workout(key: str, wid: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Fetch full workout by id; returns (workout_id, full_dict or None on failure)."""
        try:
            full = get_workout_by_id(key, wid)
            return (wid, full if isinstance(full, dict) else None)
        except Exception:
            return (wid, None)

    to_enrich: List[Tuple[int, Dict[str, Any]]] = []
    for i, w in enumerate(all_workouts):
        wid = w.get("id")
        if wid and not _workout_has_set_data(w):
            to_enrich.append((i, w))
            if MAX_ENRICH_WORKOUTS is not None and len(to_enrich) >= MAX_ENRICH_WORKOUTS:
                break

    results: Dict[str, Optional[Dict[str, Any]]] = {}
    n_to_enrich = len(to_enrich)
    if n_to_enrich > 0:
        if ENRICH_MAX_WORKERS <= 1:
            n_total = len(all_workouts)
            for i, (_idx, w) in enumerate(to_enrich):
                if (i + 1) % 5 == 0 or i == n_to_enrich - 1:
                    p = 0.40 + 0.60 * ((i + 1) / n_to_enrich)
                    report(p, f"Loading workout details… ({i + 1} / {n_to_enrich})")
                wid, full = _fetch_one_workout(api_key, w["id"])
                results[wid] = full
        else:
            completed = 0
            with ThreadPoolExecutor(max_workers=ENRICH_MAX_WORKERS) as executor:
                future_to_wid = {
                    executor.submit(_fetch_one_workout, api_key, w["id"]): w["id"]
                    for _idx, w in to_enrich
                }
                for future in as_completed(future_to_wid):
                    wid, full = future.result()
                    results[wid] = full
                    completed += 1
                    if completed % 10 == 0 or completed == n_to_enrich:
                        p = 0.40 + 0.60 * (completed / n_to_enrich)
                        report(p, f"Loading workout details… ({completed} / {n_to_enrich})")

    enriched = []
    for w in all_workouts:
        wid = w.get("id")
        if wid in results and results[wid] is not None:
            enriched.append(results[wid])
        else:
            enriched.append(w)
    all_workouts = enriched

    report(1.0, "Done.")
    workouts_raw = {**first, "workouts": all_workouts}
    df = pd.json_normalize(all_workouts) if all_workouts else pd.DataFrame()

    return {
        "user": user,
        "workouts_raw": workouts_raw,
        "workouts": all_workouts,
        "workouts_df": df,
    }


@st.cache_data(show_spinner=False, ttl=300)
def fetch_user_and_workouts(api_key: str) -> Dict[str, Any]:
    """
    Fetch user info and all workouts. Requests at least page_count pages (when
    the API provides it) so we don't miss data if an intermediate page returns
    empty/short. Also stops when a page has fewer than WORKOUTS_PER_PAGE items.
    """
    return _fetch_user_and_workouts_impl(api_key, None)
