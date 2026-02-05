-- 1) zhparser extension + chinese config
CREATE EXTENSION IF NOT EXISTS zhparser;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'chinese_zh') THEN
    CREATE TEXT SEARCH CONFIGURATION chinese_zh (PARSER = zhparser);
    ALTER TEXT SEARCH CONFIGURATION chinese_zh
      ADD MAPPING FOR n,v,a,i,e,l WITH simple;
  END IF;
END $$;

-- 2) article.search_vector
ALTER TABLE public.article
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 3) trigger function
CREATE OR REPLACE FUNCTION public.article_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
      setweight(to_tsvector('chinese_zh', coalesce(NEW.title, '')), 'A') ||
      setweight(to_tsvector('chinese_zh', coalesce(NEW.content_md, '')), 'B');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- 4) trigger
DROP TRIGGER IF EXISTS trg_article_search_vector_update ON public.article;

CREATE TRIGGER trg_article_search_vector_update
BEFORE INSERT OR UPDATE OF title, content_md
ON public.article
FOR EACH ROW
EXECUTE FUNCTION public.article_search_vector_update();

-- 5) backfill existing rows
UPDATE public.article
SET search_vector =
      setweight(to_tsvector('chinese_zh', coalesce(title, '')), 'A') ||
      setweight(to_tsvector('chinese_zh', coalesce(content_md, '')), 'B')
WHERE search_vector IS NULL;

-- 6) index
CREATE INDEX IF NOT EXISTS idx_article_search_vector_gin
ON public.article
USING GIN (search_vector);
