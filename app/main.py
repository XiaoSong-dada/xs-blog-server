from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg
import redis
from app.core.config import settings
from app.api import api_router
from app.core.exceptions import AppError
from app.schemas.base import ErrorResponse
from fastapi.responses import JSONResponse
import logging
from fastapi.staticfiles import StaticFiles
from app.core.redis import init_redis, close_redis
from app.utils.email_utils import send_mail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    try:
        yield
    finally:
        await close_redis()



app = FastAPI(
    lifespan=lifespan,
    docs_url=None if settings.IS_PRODUCTION else "/docs",
    redoc_url=None if settings.IS_PRODUCTION else "/redoc",
    openapi_url=None if settings.IS_PRODUCTION else "/openapi.json",
)
app.mount("/static", StaticFiles(directory=settings.FILE_STORAGE_PATH), name="static")

app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.code,
        content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(code=500, message="内部服务异常").model_dump(),
    )


@app.get("/")
def healthz():
    return {"status": "200", "message": "请访问从入口页访问"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    if not DATABASE_URL:
        return {"ok": False, "error": "DATABASE_URL not set"}

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                value = cur.fetchone()[0]
        return {"ok": True, "value": value}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/cache-check")
def cache_check():
    if not REDIS_URL:
        return {"ok": False, "error": "REDIS_URL not set"}

    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.set("healthz", "ok", ex=30)
        value = client.get("healthz")
        return {"ok": True, "value": value}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

