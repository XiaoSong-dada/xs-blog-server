
from app.config import settings
from app.utils.password import verify_password
from app.utils.jwt import create_jwt
from app.main import app
from app.schemas.login import LoginRequest
from app.utils.verification import isNullOrEmpty
from app.schemas.base import ErrorResponse , SuccessResponse

@app.post("/login")
def login(UserRequest: LoginRequest):

    if isNullOrEmpty(UserRequest.username) or isNullOrEmpty(UserRequest.password):
        return ErrorResponse(message="用户名或密码不能为空", code=400)

    # 获取前端传入字段
    username = UserRequest.username
    password = UserRequest.password

    


    return SuccessResponse(message="登录成功", code=200, data={"token": token})