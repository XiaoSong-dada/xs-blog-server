from app.schemas.base import Base
from uuid import UUID, uuid4
from typing import Optional
from pydantic import Field


class UserCreate(Base):
    username: str
    password: str
    email: Optional[str] = None
    nick_name: Optional[str] = None

class UserInDB(Base):
    user_id: UUID = Field(default_factory=uuid4)
    username: str
    password: str
    email: Optional[str] = None
    status: str = "1"
    is_admin: bool = False
    avatar_url: Optional[str] = None
    nick_name: Optional[str] = None
    
class UserOut(Base): 
    username: str
    email: Optional[str] = None
    status: str
    is_admin: bool
    avatar_url: Optional[str] = None
    nick_name: Optional[str] = None
