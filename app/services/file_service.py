from fastapi import UploadFile, status, File as FastApiFile
from app.core.config import settings
import os
import shutil
import uuid
import logging
from app.core.exceptions import AppError
from app.repositories.file_ropo import create_file
from app.db.transaction import transaction
from app.schemas.file import (
    File,
    FileOut,
    Session,
    UploadGroup,
    UploadError,
    UploadResult,
)
from app.utils.datetime_utils import utc_now
from app.services.upload_session_service import UploadSessionService
from typing import List, Iterable


BYTES_PER_MB = 1024 * 1024
logger = logging.getLogger(__name__)


def generate_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1]  # .jpg .png
    return f"{uuid.uuid4().hex}{ext}"


def upload_file(file: UploadFile, owner_user_id: str, bucket: str = "attachment"):
    now = utc_now()
    validate_file_or_raise(file, bucket)

    file_path = os.path.join(
        str(now.year),
        f"{now.month:02d}",
        f"{now.day:02d}",
        generate_filename(file.filename),
    )

    file_storage_path = os.path.join(settings.FILE_STORAGE_PATH, file_path)

    os.makedirs(os.path.dirname(file_storage_path), exist_ok=True)

    with open(file_storage_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_record = File(
        owner_user_id=owner_user_id,
        original_name=file.filename,
        bucket=bucket,
        stored_path=file_path,
        content_type=file.content_type,
        size=get_uploadfile_size(file),
        created_at=now,
    )

    try:
        with transaction() as conn:
            ok = create_file(conn, file_record)
            if not ok:
                raise AppError(...)
    except Exception:
        if os.path.exists(file_storage_path):
            os.remove(file_storage_path)
        raise

    return FileOut(**file_record.model_dump())


bucket_dict = {
    "image": {
        "max_bytes": 20 * BYTES_PER_MB,
        "types": (
            "image/jpeg",
            "image/png",
            "image/webp",
        ),
    },
    "markdown": {"max_bytes": 5 * BYTES_PER_MB, "types": ("text/markdown",)},
    "attachment": {"max_bytes": 20 * BYTES_PER_MB, "types": ("text/markdown",)},
    "article_markdown": {
        "max_bytes": 20 * BYTES_PER_MB,
        "types": (
            "image/jpeg",
            "image/png",
            "image/webp",
            "text/markdown",
            "text/plain",
            "application/octet-stream",
        ),
    },
}


def get_bucket_cfg(bucket: str | None) -> dict:
    # bucket 为空 or 不存在 -> 用 attachment
    if not bucket or bucket.strip() == "":
        return bucket_dict["attachment"]
    return bucket_dict.get(bucket, bucket_dict["attachment"])


def get_uploadfile_size(file: UploadFile) -> int:
    f = file.file
    pos = f.tell()
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(pos, os.SEEK_SET)
    return size


def validate_file_or_raise(file: UploadFile, bucket: str | None) -> None:
    cfg = get_bucket_cfg(bucket)

    size = get_uploadfile_size(file)
    if size > cfg["max_bytes"]:
        logger.warning("文件大小超限: size=%s, bucket=%s", size, bucket)
        raise AppError("文件大小与预期不符", code=status.HTTP_413_CONTENT_TOO_LARGE)

    if file.content_type not in cfg["types"]:
        logger.warning("文件类型不匹配: type=%s, bucket=%s", file.content_type, bucket)
        raise AppError(
            "文件类型与预期不符", code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )


def create_session() -> Session:
    now = utc_now()
    id = uuid.uuid4()
    base = "/api/file/session"
    session = Session(
        id=id,
        expires_at=now,
        upload_url=f"{base}/{id}/upload",
        commit_url=f"{base}/{id}/commit",
        status="created",
    )

    return session


async def upload_files_to_store(
    files: Iterable[UploadFile],
    bucket: str,
    session_id: str,
) -> UploadResult:
    cfg = get_bucket_cfg(bucket)
    errors: list[UploadError] = []
    uploaded: list[str] = []

    base_dir = os.path.join(
        settings.FILE_STORAGE_PATH,
        "store",
        bucket,
        session_id,
    )
    os.makedirs(base_dir, exist_ok=True)

    for file in files:
        size = get_uploadfile_size(file)
        if size > cfg["max_bytes"]:
            errors.append(UploadError(file_name=file.filename, error="文件超限"))
            continue

        if file.content_type not in cfg["types"]:
            errors.append(UploadError(file_name=file.filename, error="文件类型不匹配"))
            continue
        safe_name = os.path.basename(file.filename)
        save_path = os.path.join(base_dir, safe_name)

        try:
            with open(save_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

            await file.seek(0)
            uploaded.append(file.filename)

        except Exception as e:
            errors.append(UploadError(file_name=file.filename, error=str(e)))

    return UploadResult(uploaded=uploaded, errors=errors)


async def upload_file_session(id: str, files: List[FastApiFile]) -> UploadResult:
    # 判断当前的session是否开启
    session = await UploadSessionService.get(id)

    if not session:
        raise AppError("未找到对话", code=status.HTTP_404_NOT_FOUND)

    if session["status"] != "OPEN":
        raise AppError("本次对话已关闭", code=status.HTTP_409_CONFLICT)

    result = await upload_files_to_store(files, "article_markdown", id)
    return result
