"""add finalizada/finalizada_em/finalizada_por_user_id em vistoria_imovel"""

from alembic import op
import sqlalchemy as sa

revision = "9e8d55000cdc"
down_revision = "082ae1c5a5ae"   # confirme esse ID
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("vistoria_imovel")}

    # Adiciona apenas o que não existe
    with op.batch_alter_table("vistoria_imovel") as batch_op:
        if "finalizada" not in cols:
            batch_op.add_column(sa.Column("finalizada", sa.Boolean(), nullable=False, server_default="0"))
        if "finalizada_em" not in cols:
            batch_op.add_column(sa.Column("finalizada_em", sa.DateTime(), nullable=True))
        if "finalizada_por_user_id" not in cols:
            batch_op.add_column(sa.Column("finalizada_por_user_id", sa.Integer(), nullable=True))

    # Remove default depois (se tiver sido criado agora)
    if "finalizada" not in cols:
        with op.batch_alter_table("vistoria_imovel") as batch_op:
            batch_op.alter_column("finalizada", server_default=None)

    # Cria FK só se a coluna existe e ainda não houver FK (e não for SQLite)
    if bind.dialect.name != "sqlite" and "finalizada_por_user_id" in (c["name"] for c in insp.get_columns("vistoria_imovel")):
        # Nome fixo para conseguirmos derrubar no downgrade
        op.create_foreign_key(
            "fk_vistoria_finalizada_por_user_id",
            "vistoria_imovel",
            "user",
            ["finalizada_por_user_id"],
            ["id"],
        )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Derruba FK apenas se não for SQLite
    if bind.dialect.name != "sqlite":
        try:
            op.drop_constraint("fk_vistoria_finalizada_por_user_id", "vistoria_imovel", type_="foreignkey")
        except Exception:
            pass

    exist
