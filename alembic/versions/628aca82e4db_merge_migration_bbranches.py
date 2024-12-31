"""Merge migration bbranches

Revision ID: 628aca82e4db
Revises: 326f43b178a6, e14c81c06f61
Create Date: 2024-12-31 22:27:00.879281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '628aca82e4db'
down_revision: Union[str, None] = ('326f43b178a6', 'e14c81c06f61')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
