from app import app
from models import db, User
import json

with app.app_context():
    usuarios = User.query.all()
    dados = []

    for u in usuarios:
        dados.append({
            "email": u.email,
            "password": u.password,
            "cargo": u.cargo
        })

    with open("usuarios_backup.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print("✅ Usuários exportados com sucesso para 'usuarios_backup.json'")
