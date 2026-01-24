from app.schemas.base import Base

class LoginRequest(Base):
    username: str
    password: str