-- 引入插件
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE EXTENSION IF NOT EXISTS zhparser;

-- 创建用户表
CREATE TABLE
    IF NOT EXISTS public.users (
        user_id uuid DEFAULT gen_random_uuid () NOT NULL,
        username varchar(50) NOT NULL,
        password varchar(255) NOT NULL,
        email varchar(100),
        phone varchar(20),
        status bpchar (1),
        create_time timestamptz DEFAULT now (),
        avatar_url varchar(255),
        avatar_update_time timestamptz,
        is_admin bool DEFAULT false NOT NULL,
        nick_name varchar(20),
        CONSTRAINT users_pkey PRIMARY KEY (user_id),
        CONSTRAINT users_username_key UNIQUE (username)
    );

INSERT INTO
    users (
        username,
        password,
        email,
        phone,
        status,
        is_admin
    )
VALUES
    (
        'xiaosong',
        '$argon2id$v=19$m=65536,t=3,p=4$E+Jc6z3H2DvnvLe2FqJUag$0itzP9Mc83qIXofsKDs+SXRcJVriqbQhJDAGRMZXk10',
        'admin@example.com',
        NULL,
        '1',
        TRUE
    ) ON CONFLICT (username) DO NOTHING;

-- 创建文章表
-- public.article definition
-- Drop table
-- DROP TABLE public.article;
CREATE TABLE
    public.article (
        id uuid DEFAULT gen_random_uuid () NOT NULL,
        author_id uuid NOT NULL,
        title varchar(80) NOT NULL,
        slug varchar(120) NOT NULL,
        content_md text NULL,
        view_count int4 DEFAULT 0 NOT NULL,
        created_at timestamptz DEFAULT now () NOT NULL,
        updated_at timestamptz DEFAULT now () NOT NULL,
        published_at timestamptz NULL,
        deleted_at timestamptz NULL,
        CONSTRAINT article_pk PRIMARY KEY (id),
        CONSTRAINT article_unique UNIQUE (slug)
    );

CREATE TABLE
    public.files (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
        -- 谁上传的（可用于权限、审计、限额）
        owner_user_id uuid NOT NULL,
        -- 文件类型分类：image / markdown / avatar / attachment 等
        bucket varchar(32) NOT NULL,
        -- 原始文件名（仅用于展示）
        original_name varchar(255) NOT NULL,
        -- 实际存储路径（相对路径，不含域名）
        -- 例如：images/2026/01/31/uuid.png
        stored_path varchar(512) NOT NULL,
        -- MIME 类型
        content_type varchar(100) NOT NULL,
        -- 文件大小（字节）
        size bigint NOT NULL CHECK (size >= 0),
        -- 可选：文件指纹（用于去重/安全审计）
        sha256 char(64),
        -- 创建时间
        created_at timestamptz NOT NULL DEFAULT now (),
        -- 软删除时间（为 NULL 表示有效）
        deleted_at timestamptz,
        -- 约束：同一 bucket 下路径唯一（防止覆盖）
        CONSTRAINT files_bucket_path_uniq UNIQUE (bucket, stored_path)
    );

-- =========================
-- 索引设计
-- =========================
-- 常用：按上传者查询（管理后台、限额）
CREATE INDEX idx_files_owner_user_id ON public.files (owner_user_id);

-- 常用：按 bucket 查询（图片 / markdown）
CREATE INDEX idx_files_bucket ON public.files (bucket);

-- 常用：按创建时间排序
CREATE INDEX idx_files_created_at ON public.files (created_at DESC);

-- 可选：只查“未删除文件”的索引（提高常用查询性能）
CREATE INDEX idx_files_not_deleted ON public.files (id)
WHERE
    deleted_at IS NULL;