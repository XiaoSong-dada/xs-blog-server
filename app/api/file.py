from uuid import UUID
import logging
from fastapi.responses import FileResponse as FastAPIFileResponse
from fastapi import (
    APIRouter,
    UploadFile,
    File as FastApiFile,
    Form,
    Depends,
    status,
)
from app.security.permissions import require_login, require_admin
from app.schemas.base import (
    SuccessResponse,
    ErrorResponse,
    FileResponse,
)
from app.services.file_service import (
    upload_file,
    create_session,
    upload_file_session,
    commit_file_to_db,
    commit_file_to_db_export,
)
from app.services.upload_session_service import UploadSessionService
from typing import List
from app.schemas.file import SessionCommitParams
from pathlib import Path


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=SuccessResponse)
def upload(
    file: UploadFile = FastApiFile(...),
    bucket: str = Form("attachment"),
    _user=Depends(require_login),
):
    logger.info("before_file:%s", file)

    file_record = upload_file(file, _user.user_id, bucket)
    logger.info("file_in_server:%s", file_record)

    return SuccessResponse(message="ok", code=200, data=file_record)


@router.post("/session", response_model=SuccessResponse)
async def create(
    _user=Depends(require_admin),
):
    a = create_session()
    logger.info("session:%s", a)
    session = await UploadSessionService.create(user_id=str(_user.user_id))
    return SuccessResponse(message="ok", code=200, data=session)


@router.post("/{session_id}/upload", response_model=SuccessResponse)
async def upload_session(
    session_id: str,
    file_array: list[UploadFile] = FastApiFile(...),
    _user=Depends(require_admin),
):
    logger.info("session: %s", session_id)
    logger.info("files: %s", file_array)

    logger.info("files: %s", [f.filename for f in file_array])

    if not file_array:
        return ErrorResponse(
            code=status.HTTP_422_UNPROCESSABLE_CONTENT, message="上传文件不能为空!"
        )

    upload = await upload_file_session(session_id, file_array)
    return SuccessResponse(message="ok", code=200, data=upload)


@router.post("/{session_id}/commit", response_model=SuccessResponse)
async def commit_session(
    session_id: str,
    _user=Depends(require_admin),
):
    result = await commit_file_to_db(session_id, _user.user_id)
    logger.info("session:%s", result)
    return SuccessResponse(message="ok", code=200, data=result)


@router.post("/{session_id}/export", response_model=SuccessResponse)
async def commit_session(
    session_id: str,
    body: SessionCommitParams,
    _user=Depends(require_admin),
):
    # 强制以 path 为准（避免 body 被篡改）
    body.session_id = session_id

    result = await commit_file_to_db_export(body, _user.user_id)
    return SuccessResponse(message="ok", code=200, data=result)


@router.get("/export/sessions/{session_id}/download")
async def download_export(session_id: str, _user=Depends(require_login)):
    sess = await UploadSessionService.get(session_id)
    if not sess or sess.get("user_id") != str(_user.user_id):
        raise ErrorResponse(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if sess.get("status") != "DONE" or not sess.get("artifact_path"):
        raise ErrorResponse(status_code=status.HTTP_409_CONFLICT, detail="not ready")

    path = Path(sess["artifact_path"])
    if not path.exists():
        raise ErrorResponse(
            status_code=status.HTTP_404_NOT_FOUND, detail="file missing"
        )

    return FastAPIFileResponse(
        path=str(path), filename=path.name, media_type="application/zip"
    )
