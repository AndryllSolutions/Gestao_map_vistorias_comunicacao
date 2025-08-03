from app import create_app
from app.models import db, User
import json

app = create_app()

with app.app_context():
    with open("usuarios_backup.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    for u in dados:
        if not User.query.filter_by(email=u["email"]).first():
            novo = User(email=u["email"], password=u["password"], cargo=u.get("cargo", "usuario"))
            db.session.add(novo)

    db.session.commit()
    print("✅ Usuários importados com sucesso para o banco de dados")
