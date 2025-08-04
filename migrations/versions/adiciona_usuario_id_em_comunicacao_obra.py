"""Adiciona usuario_id na ComunicacaoObra"""

from alembic import op
import sqlalchemy as sa

# Revisões Alembic
revision = 'manual_add_usuario_id'
down_revision = None
  # Substitua pelo ID da última migração real
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('comunicacao_obra', schema=None) as batch_op:
        batch_op.add_column(sa.Column('usuario_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_usuario_comunicacao', 'user', ['usuario_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('comunicacao_obra', schema=None) as batch_op:
        batch_op.drop_constraint('fk_usuario_comunicacao', type_='foreignkey')
        batch_op.drop_column('usuario_id')
