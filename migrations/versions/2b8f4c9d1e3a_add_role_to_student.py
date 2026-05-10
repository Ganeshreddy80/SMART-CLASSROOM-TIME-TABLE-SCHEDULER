"""Add role column to student table

Revision ID: 2b8f4c9d1e3a
Revises: 9cab21ae9fcc
Create Date: 2026-05-10 09:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b8f4c9d1e3a'
down_revision = '9cab21ae9fcc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('student',
        sa.Column('role', sa.String(20),
        nullable=True, server_default='student')
    )


def downgrade():
    op.drop_column('student', 'role')
