from fastapi import FastAPI
import os
import psycopg
import redis
from app.core.config import settings

app = FastAPI()

DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL

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
