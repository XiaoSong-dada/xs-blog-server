from fastapi import APIRouter
from app.api.login import router as login_router
from app.api.users import router as users_router
from app.api.article import router as article_router
from app.api.file import router as file_router
from app.api.publish import router as publish_router
from app.api.email import router as email_router
from app.api.friend_link import router as friend_link_router
from app.api.comment import router as comment_router
from app.api.tag import router as tag_router

api_router = APIRouter()


api_router.include_router(login_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(article_router, prefix="/article", tags=["article"])
api_router.include_router(file_router, prefix="/file", tags=["file"])
api_router.include_router(publish_router, prefix="/publish", tags=["publish_article"])
api_router.include_router(email_router, prefix="/email", tags=["email"])
api_router.include_router(friend_link_router, prefix="/friend_link", tags=["friend_link"])
api_router.include_router(comment_router, prefix="/comment", tags=["comment"])
api_router.include_router(tag_router, prefix="/tag", tags=["tag"])