from fastapi import APIRouter, Depends
import logging

from app.security.permissions import require_admin
from app.schemas.base import SuccessResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserListQuery
from app.services.user_service import register_user, delete_user, get_users_page

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
def register(user: UserCreate):
    register_user(user)
    return SuccessResponse(message="register success", code=201)


@router.delete("/{user_name}", status_code=200)
def delete(user_name: str, admin_user=Depends(require_admin)):
    delete_user(user_name, admin_user=admin_user)
    return SuccessResponse(message="delete success", code=200)


@router.get("", response_model=PaginatedResponse)
def list(query: UserListQuery = Depends(), _admin=Depends(require_admin)):
    logger.info("query: %s", query)
    user_data = get_users_page(query)
    return PaginatedResponse(message="ok", code=200, **user_data)
