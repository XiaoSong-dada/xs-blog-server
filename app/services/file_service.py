from fastapi import UploadFile, status
from app.core.config import settings
import os
import shutil
import uuid
import logging
from app.core.exceptions import AppError
from app.repositories.file_ropo import create_file
from app.db.transaction import transaction
from app.schemas.file import File
from app.utils.datetime_utils import utc_now

BYTES_PER_MB = 1024 * 1024
logger = logging.getLogger(__name__)


def generate_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1]  # .jpg .png
    return f"{uuid.uuid4().hex}{ext}"


def upload_file(file: UploadFile, owner_user_id: str, bucket: str = "attachment"):

    validate_file_or_raise(file, bucket)

    file_storage_path = os.path.join(
        settings.FILE_STORAGE_PATH, generate_filename(file.filename)
    )
    os.makedirs(settings.FILE_STORAGE_PATH, exist_ok=True)
    with open(file_storage_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file = File(
        owner_user_id=owner_user_id,
        original_name=file.filename,
        bucket=bucket,
        stored_path=file_storage_path,
        content_type=file.content_type,
        size=get_uploadfile_size(file),
        created_at=utc_now(),
    )

    with transaction() as conn:
        ok = create_file(conn, file)
        if not ok:
            raise AppError(
                "记录文件数据信息失败!", code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return None


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
