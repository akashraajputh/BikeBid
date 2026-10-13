from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.auctions import router as auctions_router
from app.api.dashboard import router as dashboard_router
from app.api.motorcycles import router as motorcycles_router
from app.api.user_activity import router as user_activity_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(motorcycles_router)
api_router.include_router(auctions_router)
api_router.include_router(dashboard_router)
api_router.include_router(user_activity_router)

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(motorcycles_router)
api_v1_router.include_router(auctions_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(user_activity_router)
api_v1_router.include_router(admin_router)
