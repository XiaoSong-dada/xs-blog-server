# Alembic 数据库升级说明

本文档说明当前项目在开发环境与生产环境下的 Alembic 使用方式，并明确 `init.sql`、`stamp`、`upgrade` 三者的职责边界。

## 1. 当前结论

### 开发环境

当前开发环境 `docker-compose.yml` 已接入自动迁移流程：

- 存在独立的 `migrate` 服务
- `migrate` 启动时执行 `alembic upgrade head`
- `api` 依赖 `migrate` 成功完成后再启动

因此，开发环境执行下面命令时：

```bash
docker compose up --build
```

会自动执行：

```bash
alembic upgrade head
```

如果没有新版本，Alembic 会跳过；如果有新版本，会自动升级到最新版本。

### 生产环境

当前生产环境编排文件中没有 `migrate` 服务，因此不会自动跑 Alembic。

生产环境需要在发版时手动执行：

```bash
docker compose run --rm api alembic upgrade head
```

如果数据库是第一次接入 Alembic，且数据库本身已经存在历史表结构，则需要先执行一次：

```bash
docker compose run --rm api alembic stamp 20260311_0001
```

再执行：

```bash
docker compose run --rm api alembic upgrade head
```

## 2. `init.sql`、`stamp`、`upgrade` 的作用

### `db/init.sql`

`db/init.sql` 只会在 PostgreSQL 容器首次初始化空数据目录时执行。

当前挂载方式：

```yaml
- ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
```

含义如下：

- 第一次创建 `pg_data` 卷时会执行
- 后续普通 `docker compose up` 不会重复执行
- 如果删除数据卷后重建，例如 `docker compose down -v`，则会再次执行

### `alembic stamp`

`stamp` 只写入版本号，不执行建表和改表 SQL。

本项目里：

```bash
docker compose run --rm api alembic stamp 20260311_0001
```

表示把当前已有数据库结构标记为基线版本 `20260311_0001`。

这个操作通常只做一次。

### `alembic upgrade head`

`upgrade head` 会把数据库从当前版本升级到最新版本。

这个命令是后续数据库升级的标准入口。

## 3. 当前推荐规范

从现在开始，数据库结构变更统一走 Alembic：

- 新建版本文件：`alembic/versions/*.py`
- 升级数据库：`alembic upgrade head`
- 不再依赖新增的 `db/*.sql` 文件进行日常升级

说明：

- `db/*.sql` 可以保留为归档、备份、人工执行脚本
- 但它们不会被 Alembic 自动识别，也不会在常规升级时自动执行
- 真正参与版本管理的是 `alembic/versions/*.py`

## 4. 开发环境使用流程

### 4.1 首次接入 Alembic（已有数据库）

如果本地数据库已经由 `init.sql` 初始化过，并且此前没有 Alembic 版本记录，则执行一次：

```bash
docker compose up -d db redis
docker compose run --rm migrate alembic stamp 20260311_0001
docker compose run --rm migrate alembic upgrade head
```

执行完成后，数据库就被纳入 Alembic 管理。

### 4.2 后续开发

当你新增一个数据库变更时：

1. 新建 migration 文件
2. 编写 `upgrade()` / `downgrade()`
3. 执行升级

示例：

```bash
docker compose run --rm migrate alembic upgrade head
```

或者直接：

```bash
docker compose up --build
```

由于开发环境已接入 `migrate` 服务，重新编排时会自动检查并升级数据库。

## 5. 生产环境发布流程

### 5.1 生产环境首次接入 Alembic（已有历史库）

如果生产库已经存在表结构，但以前没有 Alembic 版本记录，推荐流程如下：

```bash
docker compose up -d db redis
docker compose run --rm api alembic stamp 20260311_0001
docker compose run --rm api alembic upgrade head
docker compose up -d api web
```

说明：

- `stamp 20260311_0001` 只需要执行一次
- `upgrade head` 用于把基线之后的 migration 补齐

### 5.2 生产环境后续发版

如果本次发版包含新的 migration，则执行：

```bash
docker compose run --rm api alembic upgrade head
docker compose up -d --build api web
```

如果本次发版不包含新的 migration，则直接发布应用即可：

```bash
docker compose up -d --build api web
```

### 5.3 生产环境何时不需要再执行 `stamp`

满足以下条件后，不要再重复执行 `stamp`：

- 数据库已经有 `alembic_version` 记录
- 当前数据库已经纳入 Alembic 管理

否则容易把版本链路打乱。

## 6. 新建升级文件的建议

建议每次变更都直接创建 Alembic 版本文件，而不是只写 `db/*.sql`。

建议命名格式：

```text
YYYYMMDD_序号_变更含义.py
```

例如：

```text
20260311_0002_tag_article_tag_sync.py
```

建议规则：

- 结构升级逻辑写在 `upgrade()`
- 回滚逻辑写在 `downgrade()`
- 对已有库兼容的建表或建索引，优先做幂等处理
- 不要直接依赖 `autogenerate` 结果，生成后必须人工审核

## 7. 常用命令

### 查看当前版本

```bash
docker compose run --rm migrate alembic current
```

生产环境：

```bash
docker compose run --rm api alembic current
```

### 查看历史版本

```bash
docker compose run --rm migrate alembic history
```

生产环境：

```bash
docker compose run --rm api alembic history
```

### 升级到最新版本

```bash
docker compose run --rm migrate alembic upgrade head
```

生产环境：

```bash
docker compose run --rm api alembic upgrade head
```

### 回滚到指定版本

```bash
docker compose run --rm migrate alembic downgrade 20260311_0001
```

生产环境：

```bash
docker compose run --rm api alembic downgrade 20260311_0001
```

## 8. 注意事项

- `db/*.sql` 不会参与 Alembic 自动升级
- `autogenerate` 在“历史库接入 Alembic”场景下容易产生误删表、误删索引、误删约束，必须人工审核
- 如果保留 `init.sql`，要明确它只负责空库初始化，不负责后续版本升级
- 开发环境当前已自动迁移，生产环境当前仍是手动迁移
- 如果后续希望生产环境也自动迁移，可以再增加一个 `migrate` 服务，并让 `api` 依赖 `migrate` 成功完成
