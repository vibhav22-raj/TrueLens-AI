from fastapi import APIRouter
from app.api.routes import auth, predict, admin, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(predict.router)
api_router.include_router(admin.router)
api_router.include_router(users.router)
