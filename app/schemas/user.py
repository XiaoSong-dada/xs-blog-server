from app.schemas.base import Base
from uuid import UUID
from typing import Optional

class UserInDB(Base):
    user_id: UUID
    username: str
    password:str
    email: Optional[str] = None
    status: str
    is_admin: bool
    avatar_url: Optional[str] = None
    nick_name: Optional[str] = None
    
class UserOut(Base): 
    username: str
    email: Optional[str] = None
    status: str
    is_admin: bool
    avatar_url: Optional[str] = None
    nick_name: Optional[str] = None
