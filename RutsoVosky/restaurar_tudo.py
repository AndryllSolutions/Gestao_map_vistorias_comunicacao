from app import create_app
from app.models import (
    db,
    User,
    ComunicacaoObra,
    VistoriaImovel,
    AgendamentoVistoria,
    HistoricoAcao,
)
import json
from datetime import datetime, date, time

def parse_datetime(obj):
    if isinstance(obj, str):
        try:
            return datetime.fromisoformat(obj)
        except:
            return obj
    return obj

app = create_app()

with app.app_context():
    # Restaurar usuários
    with open("usuarios_backup.json", "r", encoding="utf-8") as f:
        usuarios = json.load(f)
        for u in usuarios:
            if not User.query.filter_by(email=u["email"]).first():
                novo = User(email=u["email"], password=u["password"], cargo=u["cargo"])
                db.session.add(novo)

    # Restaurar comunicações
    try:
        with open("comunicacoes_backup.json", "r", encoding="utf-8") as f:
            comunicacoes = json.load(f)
            for c in comunicacoes:
                if not ComunicacaoObra.query.filter_by(nome=c["nome"], cpf=c["cpf"]).first():
                    nova = ComunicacaoObra(
                        nome=c["nome"],
                        cpf=c["cpf"],
                        endereco=c["endereco"],
                        telefone=c["telefone"],
                        comunicado=c["comunicado"],
                        economia=c["economia"],
                        assinatura=c["assinatura"],
                        tipo_imovel=c["tipo_imovel"],
                        data_envio=parse_datetime(c["data_envio"])
                    )
                    db.session.add(nova)
    except FileNotFoundError:
        print("⚠️ Arquivo comunicacoes_backup.json não encontrado. Pulando...")

    # Você pode adicionar outros blocos para VistoriaImovel, AgendamentoVistoria e HistoricoAcao

    db.session.commit()
    print("✅ Restauração concluída com sucesso.")
