"""add chat_room_id to messages

Revision ID: be16a94af9cf
Revises: c6c74c5345e0
Create Date: 2025-01-08 11:55:20.595486

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be16a94af9cf"
down_revision: Union[str, None] = "c6c74c5345e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chat_room_id가 이미 존재하므로 아무 작업도 하지 않습니다
    pass


def downgrade() -> None:
    # 이미 존재하는 컬럼이므로 제거하지 않습니다
    pass
