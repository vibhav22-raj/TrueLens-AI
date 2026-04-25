from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services import storage

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def me(user=Depends(get_current_user)):
    return storage.sanitize_user(user)


@router.get("/history")
def history(user=Depends(get_current_user)):
    return storage.get_user_history(int(user["id"]))
