import os
from typing import Any, Dict, Optional, Tuple

import requests


BASE_URL = "https://api.hevyapp.com"

LAST_AUTH_MODE: Optional[str] = None


class HevyApiError(Exception):
    """Raised when the Hevy API returns an error response."""


def get_api_key() -> Optional[str]:
    """
    Resolve the Hevy API key from environment.

    Prefer the HEVY_API_KEY env var. You should set this locally instead of
    hard-coding the key in code.
    """
    raw = os.getenv("HEVY_API_KEY")
    if raw is None:
        return None
    # Strip whitespace/newlines just in case they slipped into the .env value
    return raw.strip()


def _get_headers(api_key: str) -> Dict[str, str]:
    return {
        "Accept": "application/json",
        # Some gateways block requests without a UA.
        "User-Agent": "hevy-streamlit-dashboard/0.1",
    }


def _auth_header_variants(api_key: str) -> Tuple[Tuple[str, Dict[str, str]], ...]:
    """
    Try a few common API-key header names.

    IMPORTANT: We intentionally do NOT send `Authorization: Bearer ...` here,
    because the Hevy backend may treat that as a login token and return:
    "Invalid or expired token".
    """
    return (
        ("api-key", {"api-key": api_key}),
        ("x-api-key", {"x-api-key": api_key}),
        ("x_api_key", {"x_api_key": api_key}),  # sometimes used (less common)
    )


def hevy_get(
    path: str,
    api_key: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 15,
) -> Any:
    """
    Generic helper for GET calls to the Hevy API.
    """
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    base_headers = _get_headers(api_key)

    try:
        # Try multiple header variants; some APIs use `api-key` not `x-api-key`.
        last_resp: Optional[requests.Response] = None
        for mode, auth_headers in _auth_header_variants(api_key):
            headers = {**base_headers, **auth_headers}
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            last_resp = resp

            # Success: remember which auth header worked.
            if resp.ok:
                global LAST_AUTH_MODE
                LAST_AUTH_MODE = mode
                break

            # If unauthorized, try the next auth header variant.
            if resp.status_code == 401:
                continue

            # For any other error (403, 404, 5xx), don't hide it by retrying.
            break

        if last_resp is None:
            raise HevyApiError("No request was made to Hevy API")
        resp = last_resp
    except requests.RequestException as exc:  # network / DNS / TLS errors
        raise HevyApiError(f"Request to Hevy failed: {exc}") from exc

    if not resp.ok:
        # Try to show useful error info
        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text
        raise HevyApiError(f"Hevy API error {resp.status_code}: {payload}")

    try:
        return resp.json()
    except ValueError as exc:
        raise HevyApiError("Hevy API did not return JSON") from exc


def get_user_info(api_key: str) -> Dict[str, Any]:
    """
    Wrapper around GET /v1/user/info.
    """
    data = hevy_get("/v1/user/info", api_key=api_key)
    if not isinstance(data, dict):
        raise HevyApiError("Unexpected response shape for /v1/user/info")
    return data


def get_workouts(
    api_key: str,
    page: int = 1,
    limit: int = 50,
) -> Any:
    """
    Wrapper around GET /v1/workouts with basic pagination.

    The exact response schema may change, so the Streamlit app handles a few
    common shapes (items/data/workouts/results or a bare list).
    """
    params: Dict[str, Any] = {
        "page": page,
        "limit": limit,
    }
    return hevy_get("/v1/workouts", api_key=api_key, params=params)


def get_workout_by_id(api_key: str, workout_id: str) -> Dict[str, Any]:
    """
    Wrapper around GET /v1/workouts/{workoutId}.
    Returns full workout details (including exercises/sets) when available.
    """
    data = hevy_get(f"/v1/workouts/{workout_id}", api_key=api_key)
    if not isinstance(data, dict):
        raise HevyApiError("Unexpected response shape for /v1/workouts/{workoutId}")
    return data


def get_exercise_history(
    api_key: str,
    exercise_template_id: str,
) -> Any:
    """
    Wrapper around GET /v1/exercise_history/{exerciseTemplateId}.
    """
    path = f"/v1/exercise_history/{exercise_template_id}"
    return hevy_get(path, api_key=api_key)

