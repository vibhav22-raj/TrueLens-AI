from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
USERS_PATH = BASE_DIR / "users.json"
UPLOADS_PATH = BASE_DIR / "uploads.json"

_STORAGE_LOCK = Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(path)


def _read_json(path: Path, default_payload: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        _atomic_write_json(path, default_payload)
        return default_payload

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass

    _atomic_write_json(path, default_payload)
    return default_payload


def ensure_storage_files() -> None:
    with _STORAGE_LOCK:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _read_json(USERS_PATH, {"users": []})
        _read_json(UPLOADS_PATH, {"uploads": []})


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user.get("created_at")
    }


def list_users() -> list[dict[str, Any]]:
    ensure_storage_files()
    with _STORAGE_LOCK:
        payload = _read_json(USERS_PATH, {"users": []})
        return list(payload.get("users", []))


def get_user_by_email(email: str) -> dict[str, Any] | None:
    email_lookup = email.strip().lower()
    for user in list_users():
        if str(user.get("email", "")).lower() == email_lookup:
            return user
    return None


def get_user_by_username(username: str) -> dict[str, Any] | None:
    username_lookup = username.strip().lower()
    for user in list_users():
        if str(user.get("username", "")).lower() == username_lookup:
            return user
    return None


def create_user(
    *,
    name: str,
    email: str,
    username: str,
    hashed_password: str,
    role: str = "user"
) -> dict[str, Any]:
    ensure_storage_files()
    cleaned_email = email.strip().lower()
    cleaned_username = username.strip().lower()

    with _STORAGE_LOCK:
        payload = _read_json(USERS_PATH, {"users": []})
        users = payload.get("users", [])

        for existing in users:
            if str(existing.get("email", "")).lower() == cleaned_email:
                raise ValueError("Email already registered")
            if str(existing.get("username", "")).lower() == cleaned_username:
                raise ValueError("Username already taken")

        next_id = max((int(u.get("id", 0)) for u in users), default=0) + 1
        user = {
            "id": next_id,
            "name": name.strip() or username,
            "username": cleaned_username,
            "email": cleaned_email,
            "hashed_password": hashed_password,
            "role": role,
            "created_at": _utc_now_iso()
        }
        users.append(user)
        payload["users"] = users
        _atomic_write_json(USERS_PATH, payload)
        return user


def update_user_password(user_id: int, hashed_password: str) -> None:
    ensure_storage_files()
    with _STORAGE_LOCK:
        payload = _read_json(USERS_PATH, {"users": []})
        users = payload.get("users", [])
        for user in users:
            if int(user.get("id", -1)) == int(user_id):
                user["hashed_password"] = hashed_password
                break
        payload["users"] = users
        _atomic_write_json(USERS_PATH, payload)


def reserve_upload_id() -> int:
    ensure_storage_files()
    with _STORAGE_LOCK:
        payload = _read_json(UPLOADS_PATH, {"uploads": []})
        uploads = payload.get("uploads", [])
        return max((int(item.get("id", 0)) for item in uploads), default=0) + 1


def create_upload_record(
    *,
    upload_id: int,
    user: dict[str, Any],
    filename: str,
    file_type: str,
    result: str,
    confidence: float,
    raw_score: float,
    heatmap_url: str | None,
    note: str | None
) -> dict[str, Any]:
    ensure_storage_files()
    with _STORAGE_LOCK:
        payload = _read_json(UPLOADS_PATH, {"uploads": []})
        uploads = payload.get("uploads", [])

        if any(int(item.get("id", 0)) == upload_id for item in uploads):
            raise ValueError(f"Upload id {upload_id} already exists")

        record = {
            "id": upload_id,
            "user_id": int(user["id"]),
            "username": user["username"],
            "email": user["email"],
            "filename": filename,
            "file_type": file_type,
            "result": result,
            "confidence": float(confidence),
            "raw_score": float(raw_score),
            "heatmap_url": heatmap_url,
            "note": note,
            "created_at": _utc_now_iso()
        }

        uploads.append(record)
        payload["uploads"] = uploads
        _atomic_write_json(UPLOADS_PATH, payload)
        return record


def get_user_history(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    ensure_storage_files()
    with _STORAGE_LOCK:
        payload = _read_json(UPLOADS_PATH, {"uploads": []})
        uploads = payload.get("uploads", [])

    history = [entry for entry in uploads if int(entry.get("user_id", -1)) == int(user_id)]
    history.sort(key=lambda item: item.get("created_at", ""), reverse=True)

    transformed = []
    for item in history[:limit]:
        transformed.append(
            {
                "id": item["id"],
                "filename": item["filename"],
                "media_type": item.get("file_type", "image"),
                "created_at": item.get("created_at"),
                "prediction": {
                    "verdict": item.get("result", "UNKNOWN"),
                    "confidence": round(float(item.get("confidence", 0.0)) * 100, 2),
                    "raw_score": float(item.get("raw_score", 0.0)),
                    "heatmap_url": item.get("heatmap_url")
                },
                "note": item.get("note")
            }
        )

    return transformed


def get_system_analytics() -> dict[str, int]:
    users = list_users()
    ensure_storage_files()
    with _STORAGE_LOCK:
        uploads_payload = _read_json(UPLOADS_PATH, {"uploads": []})
    uploads = uploads_payload.get("uploads", [])
    return {
        "users": len(users),
        "uploads": len(uploads),
        "predictions": len(uploads)
    }


def sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
    return _public_user(user)
