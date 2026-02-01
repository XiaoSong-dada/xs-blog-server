from uuid import UUID
import logging
from fastapi import APIRouter, UploadFile, File as UploadField, Form, Depends
from app.security.permissions import require_login
from app.schemas.base import SuccessResponse
from app.services.file_service import upload_file

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=SuccessResponse)
def upload(
    file: UploadFile = UploadField(...),
    bucket: str = Form("attachment"),
    _user=Depends(require_login),
):
    logger.info("file:%s", file)
    logger.info("login_user:%s", _user)
    upload_file(file, _user.user_id, bucket)
    return SuccessResponse(message="ok", code=200, data="")
