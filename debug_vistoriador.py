from app import create_app, db
from app.models import VistoriaImovel, User
from datetime import datetime, time

app = create_app()

with app.app_context():
    vistoria_id = 24
    user_id = 1  # ID do vistoriador

    vistoria = VistoriaImovel.query.get(vistoria_id)

    if not vistoria:
        print(f"❌ Vistoria com ID {vistoria_id} não encontrada.")
        exit()

    # Preenchimento simulado da vistoria
    vistoria.finalizada = True
    vistoria.soleira = "positiva"
    vistoria.calcada = "cimento"
    vistoria.uso = "residencial"
    vistoria.tipo_vinculo = "proprietário"
    vistoria.responsavel_info = "João da Silva"
    vistoria.observacao_geral = "Imóvel em boas condições."

    vistoria.data_1 = datetime.strptime("2025-08-05", "%Y-%m-%d").date()
    vistoria.hora_1 = time(hour=10, minute=30)

    # Atribui o vistoriador (se ainda não tiver)
    if not vistoria.usuario_id:
        vistoria.usuario_id = user_id
        print("✅ Vistoriador atribuído.")

    db.session.commit()
    print("✅ Vistoria atualizada com sucesso!")
