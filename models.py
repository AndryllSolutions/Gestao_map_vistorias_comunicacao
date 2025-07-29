from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cargo = db.Column(db.String(50), default="usuario")  # 👈 Aqui


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


class VistoriaImovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_1 = db.Column(db.String(20))
    hora_1 = db.Column(db.String(10))
    data_2 = db.Column(db.String(20))
    hora_2 = db.Column(db.String(10))
    data_3 = db.Column(db.String(20))
    hora_3 = db.Column(db.String(10))
    
    nome_responsavel = db.Column(db.String(100)) 
    cpf_responsavel = db.Column(db.String(50))
    tipo_vinculo = db.Column(db.String(30))  # proprietário / inquilino / responsável
    
    municipio = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    rua = db.Column(db.String(100))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    celular = db.Column(db.String(20))
    
    tipo_imovel = db.Column(db.String(50))
    soleira = db.Column(db.String(50))
    calcada = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
