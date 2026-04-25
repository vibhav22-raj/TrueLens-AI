from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.services import storage

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics")
def analytics(user=Depends(require_admin)):
    return storage.get_system_analytics()
