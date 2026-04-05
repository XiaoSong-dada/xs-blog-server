# 小宋博客后端

这是小宋博客的后端服务，基于 FastAPI 构建，提供用户认证、文章管理、评论互动、标签管理、友链管理、文件上传、邮件验证码等能力，并使用 PostgreSQL 作为主数据库、Redis 作为缓存与辅助存储。

## 项目简介

后端主要负责以下能力：

- 用户登录、注册、身份鉴权与权限控制。
- 文章的创建、编辑、发布、详情查询、点赞、收藏、浏览统计。
- 评论与回复管理。
- 标签、友链、用户等后台管理接口。
- 文件上传与静态资源访问。
- 邮件验证码发送。
- 健康检查、数据库连通性检查、缓存连通性检查。

项目内置 Alembic 迁移能力，适合本地开发、Docker Compose 联调以及后续部署扩展。

## 技术栈

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Uvicorn
- Psycopg
- Pytest

## 目录说明

```text
app/
	api/           路由与接口定义
	core/          核心配置、异常、基础设施
	db/            数据库连接与会话
	models/        数据模型
	repositories/  数据访问层
	schemas/       请求与响应模型
	services/      业务服务
	utils/         工具方法

alembic/         数据库迁移脚本
compose/         Docker Compose 相关配置
db/              初始化 SQL 与数据库脚本
test/            测试用例
```

## 环境要求

- Python 3.11 及以上
- PostgreSQL 16 及以上
- Redis 7 及以上
- Docker / Docker Compose（如果采用容器方式启动）

## 环境变量

容器启动默认使用 `compose/.env`。本地启动时，也可以自行配置同名环境变量。

示例配置如下：

```env
POSTGRES_DB=icu_xiaosong_blog
POSTGRES_USER=icu_xiaosong_blog_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
DATABASE_URL=postgresql://icu_xiaosong_blog_user:URL_ENCODED_PASSWORD@127.0.0.1:5432/icu_xiaosong_blog

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_PASSWORD=
REDIS_PREFIX=blog

SECRET_KEY=replace_with_your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=300

ALLOWED_ORIGINS=["http://localhost:5173"]
FILE_STORAGE_PATH=./app/storage

EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EMAIL_CODE=your_email_authorization_code
EMAIL_SENDER=your_email@qq.com
EMAIL_FROM_NAME=小宋博客

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true
```

说明：

- 如果 `DATABASE_URL` 中的密码包含特殊字符，需要做 URL 编码，例如 `@` 转成 `%40`，`#` 转成 `%23`。
- `ALLOWED_ORIGINS` 支持 JSON 数组字符串，也支持逗号分隔字符串。
- `FILE_STORAGE_PATH` 用于后端静态文件挂载目录，接口会通过 `/static` 对外提供访问。

## 安装依赖

建议先创建虚拟环境，再安装依赖：

```bash
pip install -r requirements.txt
```

## 本地启动方式

### 1. 准备数据库与 Redis

请先确保本机 PostgreSQL 和 Redis 已启动，并且环境变量中的连接信息正确。

### 2. 执行数据库迁移

```bash
alembic upgrade head
```

### 3. 启动开发服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后可访问：

- 服务首页：http://localhost:8000/
- 健康检查：http://localhost:8000/healthz
- 数据库检查：http://localhost:8000/db-check
- Redis 检查：http://localhost:8000/cache-check

## Docker Compose 启动方式

### 1. 准备环境变量

在项目根目录确认 `compose/.env` 已存在，并按实际环境修改配置。

### 2. 启动服务

```bash
docker compose up --build
```

当前编排会启动以下服务：

- `db`：PostgreSQL 数据库。
- `redis`：Redis 缓存服务。
- `migrate`：执行 `alembic upgrade head`。
- `api`：启动 FastAPI 服务。

其中，`api` 服务依赖迁移成功后才会启动；如果迁移失败，接口服务不会拉起。

### 3. 查看迁移日志

```bash
docker compose logs migrate
```

### 4. 单独执行迁移

```bash
docker compose run --rm migrate
```

## 已有数据库接入说明

仓库中包含基线版本 `20260311_0001`，该版本不执行 DDL，适用于接管一个已经初始化完成的数据库。

第一次接入已有数据库时，可以先执行：

```bash
docker compose run --rm migrate alembic stamp 20260311_0001
```

之后再执行正常迁移：

```bash
docker compose run --rm migrate
```

## 测试

```bash
pytest
```

## 停止服务

```bash
docker compose down
```

默认情况下，`pg_data` 和 `redis_data` 数据卷会保留。

## 开发说明

- API 路由统一挂载在 `/api` 前缀下。
- 静态文件统一挂载在 `/static`。
- 跨域白名单通过 `ALLOWED_ORIGINS` 配置，前端本地开发默认允许 `http://localhost:5173`。
- 如果你同时使用 Alembic 迁移和 `db/init.sql` 初始化全量结构，需要注意避免重复建表导致冲突。
