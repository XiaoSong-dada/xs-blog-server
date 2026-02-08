from app.schemas.base import Base
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import Field
from datetime import datetime
from fastapi import UploadFile, File as UploadField
from dataclasses import dataclass


class File(Base):
    id: UUID = Field(default_factory=uuid4)
    owner_user_id: UUID
    original_name: str
    bucket: str
    stored_path: str
    content_type: str
    size: int
    sha256: Optional[str] = None
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class FileOut(Base):
    original_name: str
    stored_path: str


class Session(Base):
    id: UUID = Field(default_factory=uuid4)
    status: str
    upload_url: str
    commit_url: str
    expires_at: datetime


class UploadGroup(Base):
    file_array: List[UploadFile] = UploadField(...)


@dataclass
class UploadError:
    file_name: str
    error: str


@dataclass
class UploadResult:
    uploaded: List[str]
    errors: List[UploadError]


@dataclass
class CommitResult:
    success: List[str]
    errors: List[UploadError]


@dataclass
class SessionCommitParams:
    session_id: str
    article_ids: list[UUID]
