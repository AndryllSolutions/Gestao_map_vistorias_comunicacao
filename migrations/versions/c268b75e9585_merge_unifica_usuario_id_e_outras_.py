"""Merge: unifica usuario_id e outras alterações

Revision ID: c268b75e9585
Revises: manual_add_usuario_id, e7ce372355c1
Create Date: 2025-08-03 18:04:48.720500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c268b75e9585'
down_revision = ('manual_add_usuario_id', 'e7ce372355c1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
