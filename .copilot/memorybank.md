# 记忆库

此文件保存了 Copilot 可以跨会话参考的项目持久信息。

## 关键信息

- **项目名称：** icu.xiaosong.blog.server
- **主要语言：** Python 3.11
- **框架：** FastAPI、SQLAlchemy
- **数据库：** PostgreSQL（通过 SQLAlchemy 连接）
- **认证：** `app/security/jwt.py` 中的 JWT 令牌

## 重要模块

- `app/api` – 按功能分组的 API 端点（文章、用户等）。
- `app/repositories` – 包含仓库类的数据库访问层。
- `app/services` – 业务逻辑集中地。

已有数据库
- `db/` - 数据库升级以及已有数据库


## 编码决策

- 分页和过滤在 `pager` 工具中实现。
- 邮件服务使用 `app/services/email_service.py` 并配置 SMTP。

随着项目演进，可随时在此添加备注或架构决策。

## models/ 与 db/ 摘要

- `app/modals/friend_link.py`:
	- ORM 类 `FriendLink`，表名 `friendship_link`。
	- 字段: `id` (UUID 主键), `name`, `url`, `description`, `logo_url`, `sort_order`, `is_active`。
	- 继承 `ORMBase` 与 `TimestampMixin`（`created_at`, `updated_at` 自动维护）。

- `app/modals/article_like.py`:
	- ORM 类 `ArticleLike`，表名 `article_like`（与 `db/init.sql` 保持一致）。
	- 字段: `id` (UUID 主键), `article_id` (UUID), `user_id` (UUID), `created_at`, `deleted_at`。
	- `deleted_at` 用作软删除标记，项目中常用索引和查询会限定 `deleted_at IS NULL` 以表示“有效”记录。

- `db/init.sql`（重要表与索引要点）：
	- `users`：用户表，`user_id` UUID 主键，`username` 唯一，包含密码、email、is_admin 等字段。
	- `article`：文章表，`id` UUID 主键，`author_id`，`title`，`slug`（唯一），`content_md`，`view_count` 等。
	- `article_like`：点赞表，已在 `init.sql` 中创建：
		- 字段: `id` (UUID 主键), `article_id` (FK -> article.id), `user_id` (FK -> users.user_id), `created_at`, `deleted_at`。
		- 唯一约束 `uq_article_like (article_id, user_id)` 保证同一用户对同一文章只保留一条记录（通过软删除可表示取消点赞）。
		- 索引: `idx_article_like_article_active` 按 `article_id`（限定 `deleted_at IS NULL`），`idx_article_like_user_created_active` 按 `user_id, created_at DESC`（限定 `deleted_at IS NULL`）。
	- `article_bookmark`、`comment`、`files` 等表也包含类似的 `deleted_at` 软删除字段与常用索引策略。

备注：数据库采用部分软删除设计（`deleted_at`），常用查询会在 WHERE 中加入 `deleted_at IS NULL` 以获取“有效”记录；对计数（如点赞数）可直接 COUNT 过滤 `deleted_at IS NULL`，或考虑在文章表维护聚合计数以优化读取。

## 数据库访问风格（重要）

- 新实现的仓库请统一采用 SQLAlchemy 的异步模式 + `asyncpg` 驱动 + `alembic` 迁移，参考项目中现有的 `app/repositories/friend_link_repo.py`。
- 代码风格要点：
	- 使用 `sqlalchemy.ext.asyncio.AsyncSession` 作为 DB session 入参（例如 `async def list_all(db: AsyncSession, ...)`）。
	- 以 Repo 类或模块函数封装数据访问，返回 ORM 实体或 Pydantic/Dict，Service 层负责事务与业务组合。
	- 写入操作由 repository 执行后在 repository 或 service 中调用 `await db.commit()` / `await db.refresh(obj)`，或让调用方统一管理事务（保持一致风格）。
	- 避免新增同步 `psycopg` 直接调用风格（项目中仍有旧代码使用 psycopg，但新代码应遵循异步 SQLAlchemy 风格以便与 FastAPI 的 async 路由配合）。
	- 使用 `ON CONFLICT`、软删除（`deleted_at`）等 DB 约束时，优先用 SQLAlchemy 表达式或原始 SQL 在 AsyncSession 中执行，以保证兼容性与可读性。

示例（toggle_like 推荐签名，放在 `app/repositories/article_like_repo.py`）：

```
from sqlalchemy.ext.asyncio import AsyncSession

class ArticleLikeRepo:
		@staticmethod
		async def toggle_like(db: AsyncSession, user_id: str, article_id: str) -> tuple[bool, int]:
				# 在事务内：检查/插入/软删除并返回 (liked, count)
				...
```

把上述约定记录在 memorybank 中有助于未来贡献者保持一致实现风格。

## 新增 API 与 Service 摘要（article like）

- 路由：`POST /articles/{article_id}/like`
	- 功能：切换当前登录用户对指定文章的点赞状态（点赞/取消点赞）。
	- 鉴权：必须登录，使用 `require_login` 依赖获取当前用户（`UserInDB`）。
	- 依赖：使用 `get_db` 注入 `AsyncSession`。
	- 返回：标准 `SuccessResponse`，`data` 字段包含 `{ "liked": bool, "like_count": int }`。文章不存在返回 `ErrorResponse` (404)。

- Service：`app/services/article_like_service.py`
	- 声明方式：`class ArticleLikeService`，使用 `@staticmethod` 声明方法（与 `FriendLinkRepo` 风格相似的静态成员结构）。
	- 方法：`toggle_like(db: AsyncSession, user_id: str, article_id: str) -> (liked, count)`。
	- 职责：验证文章存在（使用 `article_repo.exists_id`），并调用仓库 `ArticleLikeRepo.toggle_like` 完成数据库切换操作。

- Repository：`app/repositories/article_like_repo.py`（已实现）
	- 使用 SQLAlchemy async API (`AsyncSession`、`select`、`update`) 实现软删除/恢复/插入逻辑。

记录以上到 memorybank 有助于后续维护与新开发者遵循统一风格。

## 文章点赞（摘要）

- 路由：`POST /articles/{article_id}/like`（位置：`app/api/article.py`）。
	- 鉴权：必须登录，使用 `require_login`（`app/security/permissions.py`）。
	- 依赖注入：`AsyncSession` 来自 `get_db`（`app/db/deps.py`）。
	- 返回：`SuccessResponse`，`data` = `{ "liked": bool, "like_count": int }`；文章不存在返回 404。

- Service（位置：`app/services/article_like_service.py`）：
	- 声明：`class ArticleLikeService`，使用 `@staticmethod`。
	- 签名：`toggle_like(db: AsyncSession, user_id: str, article_id: str) -> tuple[bool, int]`。
	- 职责：校验文章存在（使用 `ArticleRepoAsync.exists_id`），调用仓库切换点赞并返回新状态与计数。

- Repository（位置：`app/repositories/article_like_repo.py`）：
	- 声明：`class ArticleLikeRepo`，使用 `@staticmethod`。
	- 主要方法：`user_liked`, `count_likes`, `toggle_like`, `list_likes_by_user`。
	- 实现要点：基于 `AsyncSession` + SQLAlchemy ORM（`app/modals/article_like.py`），使用软删除字段 `deleted_at` 表示取消点赞；`toggle_like` 尝试软删除 -> 复原已删 -> 插入新记录的顺序，保证幂等性。

- 测试：已添加 `test/test_article_like.py`（使用 `httpx.AsyncClient` + `ASGITransport` 以避免事件循环冲突），覆盖：创建文章、点赞、取消点赞、删除文章。

- 注意事项：
	- 保持仓库风格与 `FriendLinkRepo` 一致（`AsyncSession`、`select()/scalars()`、`commit()`）。
	- 并发风险：count 操作会查询实时计数，如需高性能可在 `article` 表维护聚合 `like_count` 并在事务中更新。
	- 防刷：考虑在 service 层或网关加入速率限制/频率校验。

