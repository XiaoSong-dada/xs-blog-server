from app.schemas.base import Base

class LoginRequest(Base):
    username: str
    password: str
    captcha_token: str


class CaptchaTokenRequest(Base):
    username: str


class CaptchaTokenResponse(Base):
    captcha_token: str
    expires_in: int