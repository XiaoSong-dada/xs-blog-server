from uuid import UUID
import logging
from fastapi import APIRouter, UploadFile, File as UploadField, Form, Depends
from app.security.permissions import require_login, require_admin
from app.schemas.base import SuccessResponse
from app.services.file_service import upload_file, create_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=SuccessResponse)
def upload(
    file: UploadFile = UploadField(...),
    bucket: str = Form("attachment"),
    _user=Depends(require_admin),
):
    logger.info("before_file:%s", file)

    file_record = upload_file(file, _user.user_id, bucket)
    logger.info("file_in_server:%s", file_record)

    return SuccessResponse(message="ok", code=200, data=file_record)


@router.post("/session", response_model=SuccessResponse)
def create(
    _user=Depends(require_admin),
):
    a = create_session()
    logger.info("session:%s", a)
    return SuccessResponse(message="ok", code=200, data=a)


@router.post("/{session_id}/upload", response_model=SuccessResponse)
def upload_session(
    _user=Depends(require_admin),
):
    session = create_session()
    logger.info("session:%s", session)
    return SuccessResponse(message="ok", code=200, data=session)


@router.post("/{session_id}/commit", response_model=SuccessResponse)
def commit_session(
    _user=Depends(require_admin),
):
    session = create_session()
    logger.info("session:%s", session)
    return SuccessResponse(message="ok", code=200, data=session)
