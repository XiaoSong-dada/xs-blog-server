# Contoso Companions - Copilot 指令

## 项目概述

- **项目名**：Contoso Companions（个人博客系统）
- **主要功能**：
  - 文章的增删改查（CRUD 操作）
  - 关键字/中文拼音搜索文章
  - 用户注册与认证（JWT 令牌）
  - 已登录用户只能点赞、评论，不能修改他人文章
  - 友情链接管理

## 技术栈

```
后端框架：FastAPI + Uvicorn
数据库：PostgreSQL（SQLAlchemy ORM）+ Asyncpg（异步驱动）
缓存：Redis
认证：PyJWT + Passlib[argon2]（密码哈希）
搜索优化：PyPinyin（中文拼音转换）
数据迁移：Alembic
测试框架：Pytest + Httpx
其他：python-multipart（文件上传）
```

## 编码规范

1. **Python 风格**：遵循 PEP 8，使用 async/await 处理 I/O 操作
2. **代码结构**：
   - `app/api/` - 各功能 API 路由（article、user、login 等）
   - `app/repositories/` - 数据库访问层
   - `app/services/` - 业务逻辑层
   - `app/schemas/` - 数据验证和序列化（Pydantic）
   - `app/security/` - 认证、授权、密码管理

3. **数据库操作**：
   - 使用 SQLAlchemy ORM，避免原生 SQL
   - 所有数据库操作使用异步执行（AsyncSession）
   - 敏感查询应支持分页和过滤

4. **API 设计**：
   - 使用 RESTful 规范
   - 统一响应格式（参考现有端点）
   - 验证所有输入（Pydantic schemas）
   - 集成适当的 HTTP 状态码

5. **安全**：
   - JWT 令牌用于认证（在 `app/security/jwt.py` 中）
   - 密码使用 Argon2 哈希（Passlib）
   - 避免硬编码敏感信息
   - 记录审计日志（特别是用户操作）

6. **功能特性**：
   - 关键字搜索通过拼音匹配（PyPinyin）
   - 缓存策略用 Redis 提升查询性能
   - 文件上传处理通过 python-multipart

## 测试要求

- 使用 Pytest 编写单元测试
- Httpx 用于 HTTP 集成测试
- 测试覆盖核心业务逻辑和 API 端点

## 部署

- Docker 容器化（Dockerfile 和 docker-compose.yml）
- 通过环境变量管理配置
- 数据库初始化脚本位于 `db/` 目录

## 数据库表结构提示规则

- 当用户询问“列出库表结构”时，应首先在项目的 `db/` 目录下查找 `*.sql` 文件获取定义，然后再查看后端模型或其他来源。
