from app.schemas.base import Base
from uuid import UUID, uuid4
from typing import Optional
from pydantic import Field
from datetime import datetime


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
