"""Adiciona usuario_id na VistoriaImovel

Revision ID: 5c469f7884f1
Revises: 2eedcab624c9
Create Date: 2025-08-03 21:23:15.641960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c469f7884f1'
down_revision = '2eedcab624c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('vistoria_imovel', schema=None) as batch_op:
        batch_op.add_column(sa.Column('usuario_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_vistoria_usuario',  # nome da constraint
            'user',
            ['usuario_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('vistoria_imovel', schema=None) as batch_op:
        batch_op.drop_constraint('fk_vistoria_usuario', type_='foreignkey')
        batch_op.drop_column('usuario_id')
