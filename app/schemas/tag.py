from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    name: str = Field(..., max_length=50, description="标签名称")
    slug: str = Field(..., max_length=120, description="标签别名")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, max_length=50, description="标签名称")
    slug: str | None = Field(None, max_length=120, description="标签别名")


class TagResponse(TagBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagWithCountResponse(TagResponse):
    article_count: int = Field(0, description="关联文章数量")
