from app.schemas.base import Base
from uuid import UUID
from typing import Optional

class User(Base):
    user_id: UUID
    username: str
    email: Optional[str] = None
    status: str
    is_admin: bool
    avatar_url: Optional[str] = None
