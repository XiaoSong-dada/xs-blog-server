from app.ai.registry import register
from app.schemas.user import UserUpdate, UserInDB
from app.services.user_service import update_user


async def update_user_info_handler(current_user: UserInDB, **kwargs) -> str:
    update_fields = {}
    for field in ("nick_name", "email", "avatar_url"):
        if field in kwargs:
            update_fields[field] = kwargs[field]
    if not update_fields:
        return "没有提供任何需要更新的字段"
    user_update = UserUpdate(**update_fields)
    await update_user(current_user, user_update)
    return "用户信息更新成功"


UPDATE_USER_INFO_SCHEMA = {
    "type": "object",
    "properties": {
        "nick_name": {
            "type": "string",
            "description": "用户昵称",
        },
        "email": {
            "type": "string",
            "description": "用户邮箱地址",
        },
        "avatar_url": {
            "type": "string",
            "description": "用户头像URL",
        },
    },
}


def register_functions() -> None:
    register(
        name="update_user_info",
        description="更新当前登录用户的基本信息，包括昵称、邮箱和头像URL。所有参数都是可选的，只传需要修改的字段即可。",
        parameters=UPDATE_USER_INFO_SCHEMA,
        required_permission="require_login",
        handler=update_user_info_handler,
    )
