from fastapi import APIRouter
import logging
from app.schemas.base import SuccessResponseBase
from app.services.email_service import register_email as register_email_service
from app.schemas.email import EmailCodeRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register_email(request: EmailCodeRequest):
    logger.info(f"register email: {request}")
    await register_email_service(request.email)
    # 这里不应该进行返回验证码的，真实环境中应该发送到用户邮箱
    return SuccessResponseBase(message="成功获取邮箱", code=200)
