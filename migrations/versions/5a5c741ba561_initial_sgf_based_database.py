"""initial SGF-based database

Revision ID: 5a5c741ba561
Revises: None
Create Date: 2015-06-22 13:35:04.498787

"""

# revision identifiers, used by Alembic.
revision = '5a5c741ba561'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('black', sa.String(length=254), nullable=True),
        sa.Column('white', sa.String(length=254), nullable=True),
        sa.Column('sgf', sa.Text(), nullable=True),
        sa.Column('finished',
                  sa.Boolean(), server_default=u'0', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('games')
