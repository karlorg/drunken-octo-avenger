"""Record information about how a game finished.

Revision ID: 4623531fa2b
Revises: 9aec2a74d9
Create Date: 2016-04-16 12:27:45.788322

"""

# revision identifiers, used by Alembic.
revision = '4623531fa2b'
down_revision = '9aec2a74d9'

from alembic import op
import sqlalchemy as sa
import app.go as go

# A kind of hybrid table that contains both the old/downgraded column
# 'finished' as well as the upgraded column 'result'
gamehelper = sa.Table(
    'games',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('result', sa.Enum('WBR', 'WBC', 'BBR', 'BBC', 'D', '')),
    sa.Column('finished', sa.Boolean),
    sa.Column('sgf', sa.Text)
)

def upgrade():
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('result', sa.Enum('WBR', 'WBC', 'BBR', 'BBC', 'D', ''), nullable=True))
    connection = op.get_bind()
    for game in connection.execute(gamehelper.select()):
        result = go.get_game_result(game.sgf).value
        connection.execute(
            gamehelper.update().where(
                gamehelper.c.id == game.id
            ).values(result=result)
        )
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_column('finished')

    ### end Alembic commands ###


def downgrade():
    connection = op.get_bind()
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('finished', sa.BOOLEAN(), server_default=sa.text("'0'"), autoincrement=False, nullable=True))
    for game in connection.execute(gamehelper.select()):
        finished = game.result != ""
        connection.execute(
            gamehelper.update().where(
                gamehelper.c.id == game.id ).values(finished=finished))
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_column('result')

    ### end Alembic commands ###
