"""Add notifications, eg. for end of game.

Revision ID: 3e0919b6654
Revises: 4623531fa2b
Create Date: 2016-04-23 21:25:14.507399

"""

# revision identifiers, used by Alembic.
revision = '3e0919b6654'
down_revision = '4623531fa2b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - Adjusted (adc) ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pub_date', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('unread', sa.Boolean(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - No adjustment required (adc) ###
    op.drop_table('notifications')
    ### end Alembic commands ###