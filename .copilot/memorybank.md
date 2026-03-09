# 记忆库

此文件保存了 Copilot 可以跨会话参考的项目持久信息。

## 关键信息

- **项目名称：** icu.xiaosong.blog.server
- **主要语言：** Python 3.11
- **框架：** FastAPI、SQLAlchemy
- **数据库：** PostgreSQL（通过 SQLAlchemy 连接）
- **认证：** `app/security/jwt.py` 中的 JWT 令牌

## 本地启动与测试方式（固定约定）

- 项目使用 `docker compose` 启动，不使用本机直跑 `uvicorn`。
- 启动命令：`docker compose up -d`。
- 常用容器检查：`docker compose ps`。
- API 日志查看：`docker compose logs -f api`。
- 测试命令统一在 `api` 容器内执行，例如：
	- 单测：`docker compose exec api pytest test/test_tag.py -v`
	- 全量：`docker compose exec api pytest -v`

## 重要模块

- `app/api` – 按功能分组的 API 端点（文章、用户等）。
- `app/repositories` – 包含仓库类的数据库访问层。
- `app/services` – 业务逻辑集中地。

已有数据库
- `db/` - 数据库升级以及已有数据库
- **提示规则**：当用户请求列出数据库表结构时，优先扫描 `db/*.sql` 文件获取定义，再查看后端模型。

已有映射模型
- `app/modals` - ORM映射模型


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

## ORM 使用约定

- **异步 ORM**：统一使用 SQLAlchemy ORM 的异步模式（`AsyncSession` + `asyncpg`），避免同步 DB 调用。
- **模型位置**：所有 ORM 模型放在 `app/models`，模型继承 `ORMBase`（必要时混入 `TimestampMixin` 等）。
- **软删除**：使用 `deleted_at` 字段表示软删除，常用查询需加 `deleted_at IS NULL` 以表示“有效”记录。
- **仓库/服务分层**：数据访问放 `app/repositories`（返回 ORM 实体或 dict），业务组合与事务放 `app/services`（Service 调用 Repo 并负责校验/事务边界）。
- **切换类操作（例如 like/bookmark）**：建议 Repo 在事务内按顺序实现：先尝试软删除（取消），再尝试复原已删记录（恢复），若都未命中则插入新记录；返回 `(状态: bool, 计数: int)`。
- **事务与并发**：复杂并发场景可使用 `SELECT ... FOR UPDATE` 行级锁或在事务内按照上面顺序操作，避免重复插入或竞态。
- **测试与迁移**：对新增模型添加 Alembic 迁移并编写对应单元测试（包含并发/幂等性用例）。

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

## 评论功能（comment）

- 目标：为文章提供评论线程（root 评论 + 回复）、用户信息（昵称/头像）展示、以及按文章返回评论总数。

- 路由与接口（位置：`app/api/comment.py`）
	- `GET /api/{article_id}/comments`：分页返回文章评论线程（每条 root comment + replies 列表），响应采用 `PaginatedResponse`。
	- `POST /api/{article_id}/comments`：创建 root 评论，需要登录，返回新评论对象。
	- `POST /api/{article_id}/comments/{comment_id}/reply`：基于已有评论创建回复，需要登录，返回新回复对象。

- 后端实现要点：
	- ORM：`app/models/comment.py`（字段：`id, article_id, user_id, content, parent_id, root_id, reply_to_user_id, created_at, updated_at, deleted_at`，软删除 `deleted_at`）。
	- 仓库：`app/repositories/comment_repo.py`（异步实现）：
		- `list_article_threads(db, article_id, limit, offset)`：查询 root 评论并批量查询属于这些 root 的回复，使用 `join(User)` 将 `username/nick_name/avatar_url` 一并返回，按时间排序（root 降序、回复升序）。
		- `create_root_comment` / `create_reply_comment`：插入并返回带用户信息的 comment dict（通过 `_get_comment_with_user` join 查询）。
	- 服务：`app/services/comment_service.py`：做参数/UUID 校验、文章存在性检查（调用 ArticleRepoAsync.exists_id）以及业务组合（返回适配前端的 dict）。
	- API 层：使用 `require_login` 验证用户，捕获 `AppError` 统一返回 `ErrorResponse`。

- 文章评论计数（article.comment_count）：
	- 为了列表页展示，已在 `app/repositories/article_repo_async.py` 的 `list_article`、`list_publish_article` 和 `search_article` 中加入 `comment_count` 子查询（统计 `comment.deleted_at IS NULL`）。
	- `app/schemas/article.py` 的 `Article` / `ArticleSearchOut` 新增 `comment_count` 字段以透传给前端。

- 前端集成（web）：
	- 类型：`src/types/main.ts` 增加 `IComment`, `ICommentThread` 以及在 `IArticle`/`IArticleSearchList` 中加入 `comment_count`。
	- API：`src/api/article/article.ts` 增加 `getArticleComments`, `createArticleComment`, `replyArticleComment`。
	- Hook：`src/hook/article/useArticle.ts` 或 `useArticleComment` 提供 `fetchComments`, `createComment`, `replyComment`, `loadMore` 等方法并维护 `threads`、`loading`、`submitting`、`hasMore`。
	- 组件：实现并抽象为组件 `src/components/article/comment.list.vue`, `comment.item.vue`, `comment.body.vue`（头像+内容复用），并在文章详情页 `src/views/article/detail.vue` 中引用。

- 测试与运行：
	- 已添加集成测试 `test/test_comment.py`（流程：登录 -> 创建文章 -> 发 root 评论 -> 回复 -> 列表断言），使用项目的 docker-compose 环境运行：
		```
		docker-compose run --rm api pytest test/test_comment.py -q
		```
	- 对文章列表 `comment_count` 的回归断言已加入 `test/test_article.py`。

- 注意事项与优化建议：
	- 当前实现通过子查询实时统计 `comment_count`，在高写入量场景可考虑在 `article` 表维护聚合列来减少查询开销（需要在写评论时在事务中更新聚合列）。
	- 回复显示已通过 join 用户表获取 `nick_name` 和 `avatar_url`，若需要显示被回复用户的展示名，reply 对象应同时包含 `reply_to_user_id` 对应用户的 `nick_name`（可在仓库层额外 join）。
	- 前端可增加相对时间格式化、图片懒加载与头像占位图以提升体验。

## 标签功能（tag）更新记录

- 数据库结构：
	- `db/init.sql` 新增 `tag` 表（`id/name/slug/created_at`，`name` 与 `slug` 唯一）。
	- 新增 `article_tag` 关联表（`article_id + tag_id` 联合主键，双外键，`ON DELETE CASCADE`）。
	- 新增索引：`idx_article_tag_tag_id`，用于按标签查文章。

- ORM 模型：
	- 新增 `app/models/tag.py` 与 `app/models/article_tag.py`。
	- `app/models/article.py` 增加 `tags` 多对多关系（`secondary="article_tag"`，`lazy="selectin"`）。
	- `app/models/__init__.py` 已导出 `Tag`、`ArticleTag`。

- Schema 变更：
	- 新增 `app/schemas/tag.py`（`TagCreate/TagUpdate/TagResponse/TagWithCountResponse`）。
	- `app/schemas/article.py` 新增：
		- `Article.tags`
		- `ArticleCreated.tag_ids`
		- `ArticleUpdate.tag_ids`
		- `ArticleQuery.tag_id`（支持按标签筛选）

- Repository 与查询：
	- 新增 `app/repositories/tag_repo.py`（异步静态方法风格）：
		- `create`, `delete`, `list_all`, `get_by_id`, `get_by_name`, `get_by_slug`, `get_tags_with_count`。
	- `app/repositories/article_repo_async.py`：
		- 列表/发布列表支持 `tag_id` 过滤。
		- 列表返回中注入 `tags` 数据。
		- 创建与更新文章时支持写入/重建 `article_tag` 关联。
		- 详情查询使用 `selectinload(ArticleModel.tags)`。
	- 同步 SQL 路径同步更新：`app/repositories/article_repo.py` 与 `app/repositories/sql_builders/article_list.py` 支持 `tags` 聚合与 `tag_id` 过滤。

- Service 与 API：
	- 新增 `app/services/tag_service.py`，采用 `AppError` 统一异常风格（404/409）。
	- 新增 `app/api/tag.py`：
		- `POST /api/tag`
		- `GET /api/tag`
		- `GET /api/tag/hot`
		- `GET /api/tag/{tag_id}`
		- `PUT /api/tag/{tag_id}`
		- `DELETE /api/tag/{tag_id}`
	- `app/api/__init__.py` 已注册 `tag_router`（前缀 `/tag`）。

- 测试与验证：
	- 新增/修正 `test/test_tag.py`，采用项目现有可运行模式：`httpx.AsyncClient + ASGITransport + 登录获取 Bearer token`。
	- 已在 docker compose 环境验证通过：
		- `docker compose exec api pytest test/test_tag.py -v`
		- 结果：`4 passed`。

- 实施注意：
	- 项目当前很多接口在业务错误时返回 HTTP 200 + body 内 `code`（例如 404），标签接口测试已按该约定断言。
	- 后续新增功能优先沿用异步 SQLAlchemy 风格，避免继续扩展同步 `psycopg` 路径。


