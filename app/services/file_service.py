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
    CommitResult,
    SessionCommitParams,
)
from app.utils.datetime_utils import utc_now
from app.services.upload_session_service import UploadSessionService
from typing import List, Iterable, Dict
from app.utils.file_utils import (
    scan_md_files,
    scan_images,
    scan_md_files,
    read_md_images_map,
    replace_img_url,
    replace_md_img_urls_to_filenames,
    extract_img_urls_from_md,
    write_articles_to_dir,
    make_zip_from_dir,
    fetch_or_copy_image_to_dir,
)
from pathlib import Path
from app.schemas.article import Article, ArticleExportOut
from uuid import UUID
from app.repositories.article_repo import create_article, search_article_by_ids
from urllib.parse import urlparse
from app.utils.pinyin_utils import filename_to_slug

BYTES_PER_MB = 1024 * 1024
logger = logging.getLogger(__name__)
IMPORT_MARKDOWN_TYPE = "article_markdown"


def is_remote_url(s: str) -> bool:
    try:
        return urlparse(s).scheme in {"http", "https"}
    except Exception:
        return False


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

    result = await upload_files_to_store(files, IMPORT_MARKDOWN_TYPE, id)
    return result


async def commit_file_to_db(session_id: str, user_id: UUID):
    # 提交临时区的文件
    session = await UploadSessionService.get(session_id)
    if not session:
        raise AppError("未找到对话", code=status.HTTP_404_NOT_FOUND)

    # 用原子更新来“抢提交权”
    ok = await UploadSessionService.update_to_committing(session_id)
    if not ok:
        # 说明不是 OPEN（重复提交 / 已关闭 / 已提交）
        raise AppError("不可重复提交或会话已关闭", code=status.HTTP_409_CONFLICT)

    base_dir = os.path.join(
        settings.FILE_STORAGE_PATH,
        "store",
        IMPORT_MARKDOWN_TYPE,
        session_id,
    )
    now = utc_now()
    # 查看session中是否有图片
    md_img_mapping = read_md_images_map(base_dir)

    # 是否需要替换

    need_replace = len(md_img_mapping) > 0

    md_files = scan_md_files(base_dir)

    result = CommitResult(success=[], errors=[])

    if need_replace:
        for md_path_str, img_list in md_img_mapping.items():
            md_path = Path(md_path_str)
            old_and_new_img_mapping: dict[str, str] = {}

            for img in img_list:
                # 1) 跳过网络图片（如果你希望也处理网络图片，那是另一个流程：先下载再存）
                if is_remote_url(img):
                    continue

                # 2) 把 markdown 里的图片路径解析成真实文件路径（相对 md 所在目录）
                src_img_path = (md_path.parent / img).resolve()

                if not src_img_path.exists() or not src_img_path.is_file():
                    # 这里你可以改成 errors.append(...)
                    continue

                # 3) 用图片文件名生成新的随机文件名（保留图片扩展名）
                file_path = os.path.join(
                    str(now.year),
                    f"{now.month:02d}",
                    f"{now.day:02d}",
                    generate_filename(src_img_path.name),
                )

                dst_img_path = Path(settings.FILE_STORAGE_PATH) / file_path
                dst_img_path.parent.mkdir(parents=True, exist_ok=True)

                # 4) 复制图片到公共区（copy2 会保留时间戳等元信息；不需要可用 copyfile）
                shutil.copy2(src_img_path, dst_img_path)

                # 5) 构建替换映射：旧路径 -> 新路径（这里建议存“可访问的 URL/相对路径”，别存磁盘绝对路径）
                #    例如：/static/<file_path>  或 你自己的 CDN URL
                new_url = f"/static/{file_path.replace(os.sep, '/')}"
                old_and_new_img_mapping[img] = new_url

            # 6) 替换 md 中的图片链接（只有有映射才替换）
            if old_and_new_img_mapping:
                replace_img_url(md_path, old_and_new_img_mapping)

    for file_path in md_files:
        file = Path(file_path)

        try:
            # 1) title = 文件名（无后缀）
            title = file.stem

            # 2) slug = 文件名转拼音（中文->pinyin，用 '-'）
            slug = filename_to_slug(title, split_english_letters=False)

            # 3) content_md = 文件内容
            content_md = file.read_text(encoding="utf-8", errors="replace")

            # 4) 创建 Article
            article = Article(
                author_id=user_id,
                title=title,
                slug=slug,
                content_md=content_md,
                view_count=0,
                created_at=now,
            )

            with transaction() as conn:
                ok = create_article(conn, article)

            if ok:
                result.success.append(str(file))
            else:
                result.errors.append(
                    UploadError(file_name=str(file), error="create_article 返回 False")
                )

        except Exception as e:
            result.errors.append(UploadError(file_name=str(file), error=str(e)))

    return result


async def commit_file_to_db_export(commit_result: SessionCommitParams, user_id: UUID):
    session_id = commit_result.session_id
    session = await UploadSessionService.get(session_id)
    if not session:
        raise AppError("未找到对话", code=status.HTTP_404_NOT_FOUND)

    ok = await UploadSessionService.update_to_committing(session_id)
    if not ok:
        raise AppError("不可重复提交或会话已关闭", code=status.HTTP_409_CONFLICT)

    # 1) 查文章
    with transaction() as conn:
        articles: List[ArticleExportOut] = search_article_by_ids(
            conn, commit_result.article_ids
        )
        if not articles:
            raise AppError("未找到文章", code=status.HTTP_404_NOT_FOUND)

    # 2) 抽图 + 替换为文件名
    article_img_mapping: Dict[UUID, List[str]] = {}
    for article in articles:
        if not article.content_md:
            continue
        imgs = extract_img_urls_from_md(article.content_md)
        if imgs:
            article_img_mapping[article.id] = imgs
        article.content_md = replace_md_img_urls_to_filenames(article.content_md)

    # 3) 准备导出目录（建议不要和导入 store 混在一个目录结构）
    export_dir = Path(settings.FILE_STORAGE_PATH) / "store" / "export" / session_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # 4) 写 md 文件（title.md，重名自动 _1 _2）
    write_articles_to_dir(articles, export_dir)

    # 5) 把图片收集到 export_dir（和 md 同级）
    #    你的旧链接是 http://localhost:8000/static/....png，
    #    这里把它映射到 FILE_STORAGE_PATH 下对应的真实文件复制出来
    errors: list[UploadError] = []
    for aid, imgs in article_img_mapping.items():
        for img_url in imgs:
            saved = await fetch_or_copy_image_to_dir(
                img_url=img_url,
                export_dir=export_dir,
                file_storage_path=settings.FILE_STORAGE_PATH,
                static_prefix="/static/",
                allow_remote_download=False,  # 如果你要支持外链图片再改 True
            )
            if saved is None:
                errors.append(
                    UploadError(file_name=str(aid), error=f"图片处理失败: {img_url}")
                )

    # 6) 打 zip
    zip_path = export_dir.parent / f"articles_{session_id}.zip"
    make_zip_from_dir(export_dir, zip_path)

    # 7) 更新 session 状态为 DONE，并保存 zip 的可下载信息（建议设置 TTL）
    #    这里根据你 UploadSessionService 的实现来存：
    #    - status = DONE
    #    - artifact_path / download_url
    await UploadSessionService.update_done_with_artifact(
        session_id, artifact_path=str(zip_path)
    )
    download_url = f"/file/export/sessions/{session_id}/download"
    return {
        "session_id": session_id,
        "errors": [e.__dict__ for e in errors],
        "download_url": download_url,
    }
