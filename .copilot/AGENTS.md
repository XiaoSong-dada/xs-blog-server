# 后端工作规范 (icu.xiaosong.blog.server)
> 本文件定义了 AI 助手（GitHub Copilot / 其他 Agent）在本项目中的行为规范、编码约定与禁止事项。
> 每次开始任务前必须阅读本文件与 `memorybank.md`。
## 项目概览

- **语言：** Python 3.11
- **框架：** FastAPI
- **ORM：** SQLAlchemy（异步模式，`AsyncSession` + `asyncpg` 驱动）
- **数据库：** PostgreSQL
- **缓存：** Redis
- **认证：** JWT（`app/security/jwt.py`）
- **部署：** Docker Compose

---

## 目录结构约定

```
app/
  api/            # FastAPI 路由（每个资源独立文件，如 api/tag.py）
  core/           # 全局配置、异常、Redis 初始化
  db/             # 数据库连接、Session 工厂、依赖注入（get_db）
  models/         # SQLAlchemy ORM 模型（继承 ORMBase）
  modals/         # 旧版 ORM 模型（历史遗留，新代码用 models/）
  repositories/   # 数据库访问层（Repository 类，只做 CRUD）
  schemas/        # Pydantic 请求/响应 Schema
  security/       # 认证相关（JWT 解析、权限校验）
  services/       # 业务逻辑层（Service 类，调用 Repository，管理事务）
  storage/        # 文件存储工具
  utils/          # 通用工具（email_utils 等）
db/               # SQL 文件（建表语句、历史迁移）
test/             # pytest 单元测试
```

---

## 分层架构规范

```
Router (api/) → Service (services/) → Repository (repositories/) → DB
```

- **Router**：仅负责请求解析、权限校验（依赖注入）、调用 Service、返回响应。不写业务逻辑。
- **Service**：业务逻辑、校验、事务边界。调用一个或多个 Repository。
- **Repository**：只做数据库访问（SELECT/INSERT/UPDATE/DELETE），返回 ORM 实体或 dict。不做业务判断。

---

## ORM 模型规范

- 所有新模型放 `app/models/`，继承 `ORMBase`，必要时混入 `TimestampMixin`。
- 主键统一使用 UUID（`default=uuid.uuid4`）。
- 软删除字段使用 `deleted_at: datetime | None`，有效记录查询必须加 `WHERE deleted_at IS NULL`。

```python
# 示例：app/models/tag.py
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import ORMBase

class Tag(ORMBase):
    __tablename__ = "tag"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
```

---

## Repository 规范

- 使用静态方法（`@staticmethod`）封装每个查询操作。
- 签名第一个参数为 `db: AsyncSession`。
- 写入操作后调用 `await db.commit()` / `await db.refresh(obj)`。
- 切换类操作（点赞/收藏）：在事务内按顺序：尝试软删除 → 尝试恢复 → 插入新记录，返回 `(状态: bool, 计数: int)`。

```python
class TagRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, tag_id: UUID) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id).limit(1)
        result = await db.execute(stmt)
        return result.scalars().first()
```

---

## Schema 规范

- 所有 Schema 放 `app/schemas/`，基于 Pydantic v2（`BaseModel`）。
- 命名约定：`<Resource>Base` → `<Resource>Create` / `<Resource>Update` → `<Resource>Response`。
- 字段使用 `Field(...)` 添加校验约束（`max_length` 等）和 `description`。
- Response Schema 需设置 `model_config = ConfigDict(from_attributes=True)` 以支持 ORM 实体转换。

---

## 响应格式规范

所有端点统一返回 `SuccessResponse` 或 `ErrorResponse`（定义在 `app/schemas/base.py`）：

```python
# 成功
return SuccessResponse(message="ok", code=status.HTTP_200_OK, data=result)
# 创建成功
return SuccessResponse(message="ok", code=status.HTTP_201_CREATED, data=result)
# 错误
return ErrorResponse(message=e.message, code=e.code)
```

业务异常使用 `AppError`（`app/core/exceptions.py`），由全局 exception handler 捕获后返回 JSON。

---

## 权限校验规范

权限通过 FastAPI `Depends` 注入，统一使用 `app/security/permissions.py` 中的依赖：

| 依赖 | 用途 |
|------|------|
| `require_admin` | 需要管理员权限 |
| `require_login` | 需要登录 |
| `require_login_optional` | 登录可选（游客也可访问） |

```python
@router.post("", response_model=SuccessResponse)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserInDB = Depends(require_admin),  # 管理员权限
):
```

---

## 数据库规范

- 建表语句维护在 `db/init.sql`，历史升级脚本以日期命名（如 `db/2026_01_11_xxx.sql`）。
- **查询某张表的结构时，必须扫描 `db/` 目录下所有 `.sql` 文件的内容，从中搜索该表名对应的 `CREATE TABLE` 定义，而不是根据表名去猜测文件名。** 确认所有 SQL 文件都已检索后，若仍未找到才回退查看 `app/models/`。
- 新增表结构需同时更新 `db/init.sql` 并在 `app/models/` 中创建对应 ORM 模型。
- 常用索引策略：按业务查询字段建索引；软删除表建部分索引（`WHERE deleted_at IS NULL`）。

---

## 环境配置

所有配置从环境变量读取，集中在 `app/core/config.py` 的 `Settings` 类中，通过 `settings` 单例访问。**不要在代码中硬编码任何密钥或连接字符串。**

主要配置项：`DATABASE_URL`、`REDIS_URL`、`SECRET_KEY`、`ALGORITHM`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`ALLOWED_ORIGINS`、`FILE_STORAGE_PATH`。

---

## 常用命令

```bash
# 启动所有服务
docker compose up -d

# 查看容器状态
docker compose ps

# 查看 API 日志
docker compose logs -f api

# 运行单个测试文件
docker compose exec api pytest test/test_tag.py -v

# 运行全量测试
docker compose exec api pytest -v
```

---

## 测试规范

- 测试文件放 `test/` 目录，命名为 `test_<module>.py`。
- 使用 `conftest.py` 管理 fixtures（DB Session、测试数据等）。
- 新功能需覆盖：正常流程、边界条件、幂等性（对切换类操作尤为重要）。
