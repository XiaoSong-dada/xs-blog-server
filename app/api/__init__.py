from fastapi import APIRouter
from app.api.login import router as login_router
from app.api.users import router as users_router
from app.api.article import router as article_router
from app.api.file import router as file_router
from app.api.publish import router as publish_router
from app.api.email import router as email_router

api_router = APIRouter()


api_router.include_router(login_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(article_router, prefix="/article", tags=["article"])
api_router.include_router(file_router, prefix="/file", tags=["file"])
api_router.include_router(publish_router, prefix="/publish", tags=["publish_article"])
api_router.include_router(email_router, prefix="/email", tags=["email"])
