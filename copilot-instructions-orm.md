# ORM 使用约定（摘要）

- 使用 SQLAlchemy 异步 ORM（`AsyncSession` + `asyncpg`）。
- 将 ORM 模型放在 `app/models`，模型继承 `ORMBase`，必要时混入 `TimestampMixin`。
- 使用 `deleted_at` 字段实现软删除，常用查询应限定 `deleted_at IS NULL` 表示有效记录。
- 数据访问放 `app/repositories`，业务逻辑与事务放 `app/services`。
- 切换类操作（收藏/点赞）推荐在 Repo 内实现：先软删除 -> 再恢复已删 -> 若未命中则插入新记录；在事务内执行以保证幂等性。
- 并发风险高的场景可使用 `SELECT ... FOR UPDATE` 行级锁或在事务中保证顺序操作。
- 为新增模型添加 Alembic 迁移与对应单元测试（包含并发/幂等性用例）。
