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

## 编码决策

- 分页和过滤在 `pager` 工具中实现。
- 邮件服务使用 `app/services/email_service.py` 并配置 SMTP。

随着项目演进，可随时在此添加备注或架构决策。
