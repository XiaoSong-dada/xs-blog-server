from pydantic import BaseModel
from typing import Any

class Base(BaseModel):
    class Config:
        orm_mode = True          


class SuccessResponse(Base):
    code: int
    message: str
    data: Any|None

class ErrorResponse(Base):
    code: int
    message: str

