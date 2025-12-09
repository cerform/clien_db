"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use SQLAlchemy metadata for initial creation
    from src.db.sql_models import Base
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    # Drop all tables created by metadata (cleanup)
    from src.db.sql_models import Base
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
