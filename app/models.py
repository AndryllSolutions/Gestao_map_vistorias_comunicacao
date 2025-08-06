#from flask_sqlalchemy import SQLAlchemy
from app.extensions import db

from datetime import datetime, date, time
from app.extensions import db
from app import db
from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=True)  # <-- temporariamente
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cargo = db.Column(db.String(50), default="usuario")
    rg = db.Column(db.String(20), nullable=True)  # ✅ Adicionado aqui

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id'))
    obra = db.relationship('Obra', backref='usuarios')

class Imovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endereco = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(300))
    preco = db.Column(db.Float, nullable=False)
    imagem_url = db.Column(db.String(500))

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_imovel_obra'))
    obra = db.relationship("Obra", backref="imoveis")


class ComunicacaoObra(db.Model):
    __tablename__ = 'comunicacao_obra'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(50))
    bairro = db.Column(db.String(100))
    numero = db.Column(db.String(20))
    comunicado = db.Column(db.String(20))
    economia = db.Column(db.String(50))
    assinatura = db.Column(db.String(100))
    tipo_imovel = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_comunicacao_obra'))
    obra = db.relationship("Obra", backref="comunicacoes")

    # ✅ RELAÇÃO COM USUÁRIO
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_usuario_comunicacao'))
    usuario = db.relationship("User", backref="comunicacoes")  # ✅ AQUI
    vistorias = db.relationship("VistoriaImovel", back_populates="comunicacao", cascade="all, delete-orphan")




class VistoriaImovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_1 = db.Column(db.Date)
    hora_1 = db.Column(db.Time)
    data_2 = db.Column(db.Date)
    hora_2 = db.Column(db.Time)
    data_3 = db.Column(db.Date)
    hora_3 = db.Column(db.Time)
    nome_responsavel = db.Column(db.String(100)) 
    cpf_responsavel = db.Column(db.String(50))
    tipo_vinculo = db.Column(db.String(30))
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
    uso = db.Column(db.String(20))  # residencial, comercial, misto
    assinatura_base64 = db.Column(db.Text)  # ✅ novo campo
    finalizada = db.Column(db.Boolean, default=False)

    fotos = db.relationship("FotoVistoria", back_populates="vistoria", cascade="all, delete-orphan")
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    usuario = db.relationship('User', backref='vistorias')

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_vistoria_obra'))
    obra = db.relationship("Obra", backref="vistorias")

    comunicacao_id = db.Column(db.Integer, db.ForeignKey('comunicacao_obra.id'))
    comunicacao = db.relationship("ComunicacaoObra", back_populates="vistorias")



class AgendamentoVistoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_morador = db.Column(db.String(100), nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    data_agendada = db.Column(db.Date, nullable=False)
    hora_agendada = db.Column(db.Time, nullable=False)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_agendamento_obra'))
    obra = db.relationship("Obra", backref="agendamentos")


class HistoricoAcao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo_acao = db.Column(db.String(20))
    entidade = db.Column(db.String(50))
    entidade_id = db.Column(db.Integer)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    usuario = db.relationship("User", backref="historicos")

class Obra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    endereco = db.Column(db.String(255))
    responsavel = db.Column(db.String(100))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)



class FotoVistoria(db.Model):
    __tablename__ = 'foto_vistoria'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    descricao = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    vistoria_id = db.Column(db.Integer, db.ForeignKey('vistoria_imovel.id'), nullable=False)
    vistoria = db.relationship("VistoriaImovel", back_populates="fotos")  # ✅ aqui está o ajuste


