"""password hashes instead of plain

Revision ID: 60e49f9fa9
Revises: 18ae56e5a0f
Create Date: 2015-06-30 13:41:29.823766

"""

# revision identifiers, used by Alembic.
revision = '60e49f9fa9'
down_revision = '18ae56e5a0f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('password_hash',
                                      sa.String(length=254), nullable=True))
        batch_op.drop_column('password')


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('password',
                                      sa.VARCHAR(length=254), nullable=True))
        batch_op.drop_column('password_hash')
