from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, hash_password, password_needs_rehash, verify_password
from app.schemas.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordReset,
    LoginRequest,
    PasswordResetResponse,
    Token,
    UserCreate,
)
from app.services import password_reset, storage

router = APIRouter(prefix="/auth", tags=["auth"])


def _derive_username(name: str, email: str, explicit_username: str | None = None) -> str:
    if explicit_username and explicit_username.strip():
        return explicit_username.strip().lower()
    if name.strip():
        return name.strip().lower().replace(" ", "_")
    return email.split("@")[0].strip().lower()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate):
    username = _derive_username(payload.name, payload.email, payload.username)
    try:
        user = storage.create_user(
            name=payload.name,
            email=str(payload.email),
            username=username,
            hashed_password=hash_password(payload.password),
            role="user"
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = create_access_token(str(user["email"]), user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": storage.sanitize_user(user)
    }


@router.post("/login", response_model=Token)
def login(payload: LoginRequest):
    identity = payload.email.strip()
    user = storage.get_user_by_email(identity) or storage.get_user_by_username(identity)
    if not user or not verify_password(payload.password, str(user["hashed_password"])):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if password_needs_rehash(str(user["hashed_password"])):
        storage.update_user_password(int(user["id"]), hash_password(payload.password))
        user = storage.get_user_by_email(str(user["email"])) or user

    token = create_access_token(str(user["email"]), user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": storage.sanitize_user(user)
    }


@router.post("/forgot-password/request", response_model=PasswordResetResponse)
def forgot_password_request(payload: ForgotPasswordRequest):
    normalized_email = str(payload.email).strip().lower()
    user = storage.get_user_by_email(normalized_email)
    if not user:
        # Do not reveal account existence.
        return {
            "message": "If your email exists, an OTP has been sent.",
            "sent_to_email": True,
            "debug_otp": None,
        }

    otp = password_reset.create_otp(normalized_email)
    debug_otp = None
    sent_to_email = True

    try:
        password_reset.send_password_reset_otp(normalized_email, otp)
    except Exception:
        if not settings.otp_dev_mode:
            raise HTTPException(
                status_code=500,
                detail="Unable to send OTP email at the moment. Please try again.",
            )
        sent_to_email = False
        debug_otp = otp

    return {
        "message": "OTP sent. Please check your email.",
        "sent_to_email": sent_to_email,
        "debug_otp": debug_otp,
    }


@router.post("/forgot-password/reset", response_model=PasswordResetResponse)
def forgot_password_reset(payload: ForgotPasswordReset):
    normalized_email = str(payload.email).strip().lower()
    user = storage.get_user_by_email(normalized_email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP or email.")

    if not password_reset.verify_and_consume_otp(normalized_email, payload.otp.strip()):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    storage.update_user_password(int(user["id"]), hash_password(payload.new_password))
    return {
        "message": "Password changed successfully. Please login with your new password.",
        "sent_to_email": True,
        "debug_otp": None,
    }
