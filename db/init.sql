-- 创建用户表
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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