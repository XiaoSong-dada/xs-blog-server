-- public.users definition
-- Drop table
-- DROP TABLE public.users;
CREATE TABLE
    public.users (
        user_id uuid DEFAULT gen_random_uuid () NOT NULL,
        username varchar(50) NOT NULL,
        "password" varchar(128) NOT NULL,
        email varchar(100) NULL,
        phone varchar(20) NULL,
        status bpchar (1) NULL,
        create_time timestamptz DEFAULT now () NULL,
        avatar_url varchar(255) NULL,
        avatar_update_time timestamptz NULL,
        is_admin bool DEFAULT false NOT NULL,
        CONSTRAINT users_pkey PRIMARY KEY (user_id),
        CONSTRAINT users_username_key UNIQUE (username)
    );

-- Insert admin user
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
        'admin',
        '$argon2id$v=19$m=65536,t=3,p=4$6bZ5Q3lVbGJzU1F6bTJiMA$X9p4r+1bP9Zq1Z6tP3s9+XrWcH6Kq1N3R5Z6QKc8y9M',
        'admin@example.com',
        NULL,
        '1',
        TRUE
    );