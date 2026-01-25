from passlib.context import CryptContext


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.hash(password)