"""Add is_founder field to users table

Revision ID: b6906a2f3b28
Revises: 45ca65d842ad
Create Date: 2025-07-29 13:10:55.242442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6906a2f3b28'
down_revision = '45ca65d842ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_founder', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_founder')

    # ### end Alembic commands ###
