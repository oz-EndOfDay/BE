"""Merging migration branches

Revision ID: 0b1202e0109c
Revises: 2f9d23dc2603, 98a55a606049
Create Date: 2025-01-03 23:32:32.086907

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b1202e0109c"
down_revision: Union[str, None] = ("2f9d23dc2603", "98a55a606049")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
