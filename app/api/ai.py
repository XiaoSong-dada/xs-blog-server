from fastapi import APIRouter, Depends
from app.schemas.base import Base, SuccessResponse
from app.schemas.user import UserInDB
from app.security.permissions import require_login
from app.services.ai_service import chat_with_deepseek
from app.ai.functions import register_functions

register_functions()

router = APIRouter()


class DeepSeekConfig(Base):
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"


class AIChatRequest(Base):
    messages: list[dict]
    config: DeepSeekConfig


class AIChatResponse(Base):
    reply: str
    error: bool = False


@router.post("/chat", response_model=SuccessResponse)
async def ai_chat(
    request: AIChatRequest,
    user: UserInDB = Depends(require_login),
) -> SuccessResponse:
    result = await chat_with_deepseek(
        messages=request.messages,
        api_key=request.config.api_key,
        base_url=request.config.base_url,
        model=request.config.model,
        user=user,
    )
    return SuccessResponse(
        code=200,
        message="ok",
        data=AIChatResponse(**result).model_dump(),
    )
