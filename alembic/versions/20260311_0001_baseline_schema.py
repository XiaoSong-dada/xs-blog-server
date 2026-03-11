"""baseline schema marker

Revision ID: 20260311_0001
Revises:
Create Date: 2026-03-11 00:01:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260311_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline-only revision: keep empty to adopt existing schema via `alembic stamp`.
    pass


def downgrade() -> None:
    pass
