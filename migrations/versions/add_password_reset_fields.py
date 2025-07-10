"""Add password reset fields to User model

Revision ID: 7d8f90a15bc2
Revises: 6c5f80a02eb0
Create Date: 2025-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d8f90a15bc2'
down_revision = '6c5f80a02eb0'
branch_labels = None
depends_on = None

def upgrade():
    # Add password reset fields to users table
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))
    
    # Create unique index on password_reset_token
    op.create_index(op.f('ix_users_password_reset_token'), 'users', ['password_reset_token'], unique=True)

def downgrade():
    # Remove the columns and index
    op.drop_index(op.f('ix_users_password_reset_token'), table_name='users')
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
