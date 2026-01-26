from app.schemas.base import Base
from pydantic import Field

class PageQuery(Base):
    limit: int = Field(default=10, ge=1, le=100)   # 限制最大值，防止一次查爆
    offset: int = Field(default=0, ge=0)