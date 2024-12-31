"""craeate diaries table

Revision ID: e14c81c06f61
Revises: 9ea12a8244d9
Create Date: 2024-12-30 17:12:58.721315

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e14c81c06f61"
down_revision: Union[str, None] = "9ea12a8244d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "diaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("write_date", sa.Date(), nullable=False),
        sa.Column(
            "weather",
            sa.Enum(
                "clear", "some_clouds", "cloudy", "rainy", "snowy", name="weatherenum"
            ),
            nullable=True,
        ),
        sa.Column(
            "mood",
            sa.Enum("happy", "good", "normal", "tired", "sad", name="moodenum"),
            nullable=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("img_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("diaries")
    # ### end Alembic commands ###