from pydantic import BaseModel, ConfigDict
from typing import Any , Optional


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SuccessResponseBase(Base):
    code: int
    message: str


class SuccessResponse(SuccessResponseBase):
    data: Any | None = None

class SuccessResponseNoPage(SuccessResponse):
    total: int


class ErrorResponse(Base):
    code: int
    message: str


class PaginatedResponse(SuccessResponse):
    limit: int
    offset: int
    total: int


class FileResponse(Base):
    path: str
    filename: str
    media_type: str
