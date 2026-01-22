# icu.xiaosong.blog.server

FastAPI backend with Postgres as the primary database and Redis as cache. Deploy via Docker Compose.

## Deployment (Docker Compose)

### 1) Prerequisites

- Install Docker and Docker Compose (Docker Desktop is OK)

### 2) Configure environment variables

The project uses `compose/.local.env` as the container env file (referenced in `docker-compose.yml`).

Ensure these variables exist (adjust as needed):

```
POSTGRES_DB=icu_xiaosong_blog
POSTGRES_USER=icu_xiaosong_blog_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://icu_xiaosong_blog_user:URL_ENCODED_PASSWORD@db:5432/icu_xiaosong_blog

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379/0
```

If the password contains special characters, URL-encode it in `DATABASE_URL` (e.g. `@` -> `%40`, `#` -> `%23`).

### 3) Start services

From the project root:

```
docker compose up --build
```

### 4) Verify

- `http://localhost:8000/healthz`
- `http://localhost:8000/db-check`
- `http://localhost:8000/cache-check`

### 5) Stop services

```
docker compose down
```

Volumes `pg_data` and `redis_data` are kept by default.
