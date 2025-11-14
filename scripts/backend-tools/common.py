#!/usr/bin/env python3
"""
Shared helpers for backend utility scripts.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def _base_url() -> str:
    base = API_BASE_URL.strip() or "http://localhost:8000/api/v1"
    return base.rstrip("/")


def api_url(path: str) -> str:
    return f"{_base_url()}/{path.lstrip('/')}"


def request_json(method: str, path: str, token: str | None = None, payload: Any | None = None) -> Any:
    url = api_url(path)
    headers = {"Accept": "application/json"}
    data: bytes | None = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if not raw:
                return {}
            text = raw.decode("utf-8")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover - diagnostic path
            detail = ""
        message = f"{exc.code} {exc.reason}"
        if detail:
            message = f"{message}: {detail}"
        raise RuntimeError(message) from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from None


def login_by_max_id(max_id: int) -> str:
    params = urllib.parse.urlencode({"max_id": int(max_id)})
    data = request_json("GET", f"/auth/login-by-max-id?{params}")
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Login response does not contain access_token")
    return token


def require_max_id(cli_value: int | None, *, env_name: str = "ADMIN_MAX_ID") -> int:
    if cli_value is not None:
        return int(cli_value)
    env_value = os.getenv(env_name)
    if not env_value:
        raise RuntimeError(
            f"Set --max-id or define {env_name} so the script knows which MAX ID to use."
        )
    return int(env_value)


def pretty_print(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def pick_first(items: Iterable[dict], label: str) -> dict:
    try:
        return next(iter(items))
    except StopIteration:
        raise RuntimeError(f"No {label} available in the backend database") from None

