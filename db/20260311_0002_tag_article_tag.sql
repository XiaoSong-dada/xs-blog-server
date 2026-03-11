-- =========================
-- 标签表：tag
-- =========================
CREATE TABLE
    IF NOT EXISTS public.tag (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
        name varchar(50) NOT NULL,
        slug varchar(120) NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now (),
        CONSTRAINT tag_name_unique UNIQUE (name),
        CONSTRAINT tag_slug_unique UNIQUE (slug)
    );

-- =========================
-- 文章-标签关联表：article_tag
-- =========================
CREATE TABLE
    IF NOT EXISTS public.article_tag (
        article_id uuid NOT NULL,
        tag_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now (),
        CONSTRAINT pk_article_tag PRIMARY KEY (article_id, tag_id),
        CONSTRAINT fk_article_tag_article FOREIGN KEY (article_id) REFERENCES public.article (id) ON DELETE CASCADE,
        CONSTRAINT fk_article_tag_tag FOREIGN KEY (tag_id) REFERENCES public.tag (id) ON DELETE CASCADE
    );

-- 常用索引：按标签查文章
CREATE INDEX IF NOT EXISTS idx_article_tag_tag_id ON public.article_tag (tag_id);


