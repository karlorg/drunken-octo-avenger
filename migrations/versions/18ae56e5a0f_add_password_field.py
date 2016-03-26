"""add password field

Revision ID: 18ae56e5a0f
Revises: 43e4e3402b9
Create Date: 2015-06-29 19:31:39.056586

"""

# revision identifiers, used by Alembic.
revision = '18ae56e5a0f'
down_revision = '43e4e3402b9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(
            sa.Column('password', sa.String(length=254), nullable=True))


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('password')
