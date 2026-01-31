from fastapi import UploadFile
from app.core.config import settings
import os
import shutil
import uuid


def generate_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1]  # .jpg .png
    return f"{uuid.uuid4().hex}{ext}"


def upload_file(file: UploadFile, ower_user_id: str):
    file_storage_path = os.path.join(
        settings.FILE_STORAGE_PATH, generate_filename(file.filename)
    )
    user_id = ower_user_id  # 这个用户名后续再用
    os.makedirs(settings.FILE_STORAGE_PATH, exist_ok=True)
    with open(file_storage_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return None
