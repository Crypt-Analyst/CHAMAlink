"""Remove SACCO_NGO plan type

Revision ID: 6c5f80a02eb0
Revises: 47e956906613
Create Date: 2025-07-10 02:53:22.533916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c5f80a02eb0'
down_revision = '47e956906613'
branch_labels = None
depends_on = None


def upgrade():
    # First delete any SACCO_NGO plans
    op.execute("DELETE FROM enterprise_subscription_plans WHERE plan_type = 'SACCO_NGO'")
    
    # Remove SACCO_NGO from the enum
    # Note: PostgreSQL doesn't support removing enum values directly
    # We need to recreate the enum type
    op.execute("ALTER TYPE plantype RENAME TO plantype_old")
    op.execute("CREATE TYPE plantype AS ENUM ('BASIC', 'ADVANCED', 'ENTERPRISE')")
    op.execute("ALTER TABLE enterprise_subscription_plans ALTER COLUMN plan_type TYPE plantype USING plan_type::text::plantype")
    op.execute("DROP TYPE plantype_old")


def downgrade():
    # Add SACCO_NGO back to the enum
    op.execute("ALTER TYPE plantype RENAME TO plantype_old")
    op.execute("CREATE TYPE plantype AS ENUM ('BASIC', 'ADVANCED', 'ENTERPRISE', 'SACCO_NGO')")
    op.execute("ALTER TABLE enterprise_subscription_plans ALTER COLUMN plan_type TYPE plantype USING plan_type::text::plantype")
    op.execute("DROP TYPE plantype_old")
