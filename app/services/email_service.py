from app.core.redis import get_redis
import random
import re
from app.core.exceptions import AppError
from fastapi import status
from app.utils.email_utils import send_mail


async def request_email_code(email: str) -> str | None:
    redis = get_redis()

    # 1) 先抢“冷却锁”（原子操作：同一时刻只有一个能成功）
    cooldown_key = f"email:cooldown:{email}"
    ok = await redis.set(cooldown_key, "1", nx=True, ex=60)
    if not ok:
        return None  # 60 秒内已经发过了（或正在发）

    # 2) 生成 4 位数字验证码（更符合常见验证码）
    code = f"{random.randint(0, 9999):04d}"

    # 3) 存验证码（90 秒有效，你想 100 秒也可以）
    code_key = f"email:code:{email}"
    await redis.set(code_key, code, ex=90)

    return code


async def verify_email_code(email: str, code: str) -> bool:
    redis = get_redis()
    code_key = f"email:code:{email}"
    stored_code = await redis.get(code_key)
    if stored_code != code:
        return False

    # 验证通过后删除验证码，防止重复使用
    await redis.delete(code_key)
    return True


async def register_email(email: str) -> str:

    # 这段邮箱校验好像有问题，当格式不正确时速度贼慢
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise AppError("邮箱格式不正确", code=status.HTTP_400_BAD_REQUEST)

    code = await request_email_code(email)

    if not code:
        raise AppError("请勿频繁请求验证码", code=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # 将验证发发送至邮箱
    
    await send_mail(
        subject="验证码发送测试",
        content=f"你的验证码是: {code}",
        to_email=email,
    )
    return code