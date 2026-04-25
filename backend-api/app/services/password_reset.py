from __future__ import annotations

import hashlib
import json
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from threading import Lock

from app.core.config import settings

OTP_PATH = Path(__file__).resolve().parents[2] / "data" / "password_reset_otps.json"
_OTP_LOCK = Lock()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(path)


def _read_json(path: Path) -> dict:
    default_payload = {"entries": []}
    if not path.exists():
        _atomic_write_json(path, default_payload)
        return default_payload
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            loaded.setdefault("entries", [])
            return loaded
    except json.JSONDecodeError:
        pass
    _atomic_write_json(path, default_payload)
    return default_payload


def _hash_otp(email: str, otp: str) -> str:
    key = f"{email.strip().lower()}::{otp.strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def create_otp(email: str) -> str:
    normalized_email = email.strip().lower()
    otp = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = (_utc_now() + timedelta(minutes=settings.otp_expire_minutes)).isoformat()
    otp_hash = _hash_otp(normalized_email, otp)

    with _OTP_LOCK:
        payload = _read_json(OTP_PATH)
        entries = payload.get("entries", [])
        now = _utc_now()

        # Keep only active entries from now onwards.
        retained = []
        for entry in entries:
            try:
                expiry = datetime.fromisoformat(str(entry.get("expires_at")))
            except ValueError:
                continue
            if expiry > now and not bool(entry.get("used", False)):
                retained.append(entry)

        retained.append(
            {
                "email": normalized_email,
                "otp_hash": otp_hash,
                "expires_at": expires_at,
                "used": False,
                "created_at": _utc_now_iso(),
            }
        )
        payload["entries"] = retained
        _atomic_write_json(OTP_PATH, payload)

    return otp


def verify_and_consume_otp(email: str, otp: str) -> bool:
    normalized_email = email.strip().lower()
    otp_hash = _hash_otp(normalized_email, otp)
    now = _utc_now()

    with _OTP_LOCK:
        payload = _read_json(OTP_PATH)
        entries = payload.get("entries", [])
        matched = False
        updated_entries = []

        for entry in entries:
            if entry.get("email") != normalized_email:
                updated_entries.append(entry)
                continue

            try:
                expiry = datetime.fromisoformat(str(entry.get("expires_at")))
            except ValueError:
                continue

            if expiry <= now:
                continue

            is_same_otp = entry.get("otp_hash") == otp_hash and not bool(entry.get("used", False))
            if is_same_otp and not matched:
                matched = True
                entry["used"] = True
                entry["used_at"] = _utc_now_iso()
            updated_entries.append(entry)

        payload["entries"] = updated_entries
        _atomic_write_json(OTP_PATH, payload)
        return matched


def send_password_reset_otp(email: str, otp: str) -> None:
    if not settings.smtp_host:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = "DeepShield Password Reset OTP"
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(
        "Your DeepShield OTP is: "
        f"{otp}\n\n"
        f"This OTP expires in {settings.otp_expire_minutes} minutes.\n"
        "If you did not request a password reset, ignore this message."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)

