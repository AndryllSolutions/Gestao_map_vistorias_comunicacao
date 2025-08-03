from app import create_app
from app.models import (
    db,
    User,
    Imovel,
    ComunicacaoObra,
    VistoriaImovel,
    AgendamentoVistoria,
    HistoricoAcao,
)
import json
import os
from datetime import datetime, date, time

def serialize(obj):
    """Converte objeto SQLAlchemy em dict e formata datetime, date e time"""
    data = {}
    for col in obj.__table__.columns:
        valor = getattr(obj, col.name)
        if isinstance(valor, (datetime, date)):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(valor, time):
            valor = valor.strftime("%H:%M:%S")
        data[col.name] = valor
    return data

def serialize(obj):
    """Converte objeto SQLAlchemy em dict e formata datetime, date e time"""
    data = {}
    for col in obj.__table__.columns:
        valor = getattr(obj, col.name)
        if isinstance(valor, (datetime, date)):
            valor = valor.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(valor, time):
            valor = valor.strftime("%H:%M:%S")
        data[col.name] = valor
    return data

app = create_app()

with app.app_context():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"backup_completo_{timestamp}.json")

    dados = {
        "usuarios": [serialize(u) for u in User.query.all()],
        "imoveis": [serialize(i) for i in Imovel.query.all()],
        "comunicacoes": [serialize(c) for c in ComunicacaoObra.query.all()],
        "vistorias": [serialize(v) for v in VistoriaImovel.query.all()],
        "agendamentos": [serialize(a) for a in AgendamentoVistoria.query.all()],
        "historico": [serialize(h) for h in HistoricoAcao.query.all()],
    }

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"✅ Backup salvo com sucesso em: {backup_path}")
