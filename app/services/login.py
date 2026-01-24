
from app.config import settings
from fastapi import FastAPI, HTTPException
from app.database import get_user_by_username
from app.utils.password import verify_password
from app.utils.jwt import create_jwt
app = FastAPI()

@app.post("/login")
def login(username: str, password: str):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token_data = {
        "sub": user.username,
        "is_admin": user.is_admin
    }
    token = create_jwt(token_data)
    return {"access_token": token, "token_type": "bearer"}