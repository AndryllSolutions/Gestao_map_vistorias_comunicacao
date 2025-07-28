from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Imovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endereco = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(300))
    preco = db.Column(db.Float, nullable=False)
    imagem_url = db.Column(db.String(500))  # Novo campo para a URL da imagem
    
class ComunicacaoObra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(50))
    comunicado = db.Column(db.String(20))  # Presencial, Panfleto, WhatsApp
    economia = db.Column(db.String(50))
    assinatura = db.Column(db.String(100))
    tipo_imovel = db.Column(db.String(200))  # Ex: Casa, Comércio, etc
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
