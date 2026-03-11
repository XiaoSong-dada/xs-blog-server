"""tag and article_tag sync

Revision ID: 20260311_0002
Revises: 20260311_0001
Create Date: 2026-03-11 04:05:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260311_0002"
down_revision: Union[str, Sequence[str], None] = "20260311_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep this migration idempotent for stamped existing databases.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.tag (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name varchar(50) NOT NULL,
            slug varchar(120) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT tag_name_unique UNIQUE (name),
            CONSTRAINT tag_slug_unique UNIQUE (slug)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.article_tag (
            article_id uuid NOT NULL,
            tag_id uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT pk_article_tag PRIMARY KEY (article_id, tag_id),
            CONSTRAINT fk_article_tag_article
                FOREIGN KEY (article_id) REFERENCES public.article (id) ON DELETE CASCADE,
            CONSTRAINT fk_article_tag_tag
                FOREIGN KEY (tag_id) REFERENCES public.tag (id) ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_article_tag_tag_id
        ON public.article_tag (tag_id)
        """
    )


def downgrade() -> None:
    # Intentionally non-destructive to avoid dropping business tables by mistake.
    pass
