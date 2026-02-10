from app.schemas.base import Base
from app.schemas.params import PageQuery
from uuid import UUID, uuid4
from typing import Optional
from dataclasses import dataclass
from pydantic import Field


class UserCreate(Base):
    username: str
    password: str
    email: Optional[str] = None
    nick_name: Optional[str] = None
    code: Optional[str] = None  # 用于邮箱注册时的验证码


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
    user_id: UUID = Field(default_factory=uuid4)
    username: str
    email: Optional[str] = None
    status: str
    is_admin: bool
    avatar_url: Optional[str] = None
    nick_name: Optional[str] = None


class UserListQuery(PageQuery):
    username: str | None = None
    email: str | None = None
    nick_name: str | None = None
    is_admin: bool | None = None

class UserUpdate(Base):
    email: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserUpdatePassword(Base):
    old_password:str
    password:str