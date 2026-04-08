from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.deps import get_db
from app.schemas.login import CaptchaTokenRequest, CaptchaTokenResponse, LoginRequest
from app.utils.verification import is_null_or_empty
from app.schemas.base import ErrorResponse , SuccessResponse
from app.services.auth_service import authenticate_user
from app.services.captcha_token_service import CaptchaTokenService

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/captcha/token")
async def issue_captcha_token(payload: CaptchaTokenRequest, request: Request):
    if is_null_or_empty(payload.username):
        return ErrorResponse(message="用户名不能为空", code=400)

    token, expires_in = await CaptchaTokenService.issue_token(
        username=payload.username,
        client_ip=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    data = CaptchaTokenResponse(captcha_token=token, expires_in=expires_in)
    return SuccessResponse(message="验证码校验通过", code=200, data=data.model_dump())


@router.post("/login")
async def login(UserRequest: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):

    if (
        is_null_or_empty(UserRequest.username)
        or is_null_or_empty(UserRequest.password)
        or is_null_or_empty(UserRequest.captcha_token)
    ):
        return ErrorResponse(message="用户名、密码或验证码凭证不能为空", code=400)

    # 获取前端传入字段
    username = UserRequest.username
    password = UserRequest.password
    captcha_token = UserRequest.captcha_token

    captcha_ok, captcha_reason = await CaptchaTokenService.consume_and_validate(
        captcha_token=captcha_token,
        username=username,
        client_ip=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    if not captcha_ok:
        message = "验证码凭证无效或已过期"
        if captcha_reason == "binding_mismatch":
            message = "验证码凭证与当前登录环境不匹配"
        return ErrorResponse(message=message, code=403)

    authenticate_user_result = await authenticate_user(db, username, password)

    if not authenticate_user_result:
        return ErrorResponse(message="用户名或密码错误", code=401)

    return SuccessResponse(message="登录成功", code=200, data={"token": authenticate_user_result})