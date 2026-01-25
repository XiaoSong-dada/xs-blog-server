from pydantic import BaseModel, ConfigDict
from typing import Any

class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    
class SuccessResponse(Base):
    code: int
    message: str
    data: Any | None = None

class ErrorResponse(Base):
    code: int
    message: str

