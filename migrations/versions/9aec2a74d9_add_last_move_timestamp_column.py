"""add last-move timestamp column

Revision ID: 9aec2a74d9
Revises: 60e49f9fa9
Create Date: 2016-03-17 16:31:34.994097

"""

# revision identifiers, used by Alembic.
revision = '9aec2a74d9'
down_revision = '60e49f9fa9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('games') as batch_op:
        batch_op.add_column(sa.Column('last_move_time', sa.DateTime()))


def downgrade():
    with op.batch_alter_table('games') as batch_op:
        batch_op.drop_column(sa.Column('last_move_time'))
