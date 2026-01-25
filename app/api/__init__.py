from fastapi import APIRouter
from app.api.login import router as login_router
from app.api.users import router as users_router

api_router = APIRouter()


api_router.include_router(login_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])