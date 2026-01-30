from fastapi import APIRouter

from app.api.routes import auth, channel_managers, channels, health

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(channels.router)
api_router.include_router(channel_managers.router)
api_router.include_router(health.router)
