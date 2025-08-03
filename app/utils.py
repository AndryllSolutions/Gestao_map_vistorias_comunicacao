from .models import HistoricoAcao, db


def registrar_acao(usuario_id, tipo_acao, entidade, entidade_id, observacao=""):
    """Registra uma ação realizada por um usuário no banco de dados."""
    acao = HistoricoAcao(
        usuario_id=usuario_id,
        tipo_acao=tipo_acao,
        entidade=entidade,
        entidade_id=entidade_id,
        observacao=observacao,
    )
    db.session.add(acao)
    db.session.commit()
