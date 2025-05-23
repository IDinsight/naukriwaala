"""Initial migration

Revision ID: 39bf69aadd68
Revises:
Create Date: 2025-04-02 12:03:50.106740

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "39bf69aadd68"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "establishments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("establishment_name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("registration_type", sa.String(), nullable=True),
        sa.Column("working_days", sa.String(), nullable=True),
        sa.Column("state_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("short_description", sa.String(), nullable=True),
        sa.Column("naps_benefit", sa.Boolean(), nullable=True),
        sa.Column("number_of_vacancies", sa.Integer(), nullable=True),
        sa.Column("available_vacancies", sa.Integer(), nullable=True),
        sa.Column("gender_type", sa.String(), nullable=True),
        sa.Column("stipend_from", sa.Integer(), nullable=True),
        sa.Column("stipend_upto", sa.Integer(), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=True),
        sa.Column("approval_status", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("establishment_id", sa.String(), nullable=True),
        sa.Column("course_data", sa.JSON(), nullable=True),
        sa.Column("trainings_data", sa.JSON(), nullable=True),
        sa.Column("locations_data", sa.JSON(), nullable=True),
        sa.Column("last_checked", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["establishment_id"],
            ["establishments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("opportunities")
    op.drop_table("establishments")
    # ### end Alembic commands ###
