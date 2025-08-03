from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cargo = db.Column(db.String(50), default="usuario")
#
    # Relacionamento com Obra
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
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(50))
    comunicado = db.Column(db.String(20))
    economia = db.Column(db.String(50))
    assinatura = db.Column(db.String(100))
    tipo_imovel = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_comunicacao_obra'))
    obra = db.relationship("Obra", backref="comunicacoes")


class VistoriaImovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_1 = db.Column(db.Date)        # ALTERADO
    hora_1 = db.Column(db.Time)        # ALTERADO
    data_2 = db.Column(db.Date)        # ALTERADO
    hora_2 = db.Column(db.Time)        # ALTERADO
    data_3 = db.Column(db.Date)        # ALTERADO
    hora_3 = db.Column(db.Time)        # ALTERADO
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
    fotos = db.relationship("FotoVistoria", back_populates="vistoria", cascade="all, delete-orphan")
    finalizada = db.Column(db.Boolean, default=False)

    obra_id = db.Column(db.Integer, db.ForeignKey('obra.id', name='fk_vistoria_obra'))
    obra = db.relationship("Obra", backref="vistorias")
    comunicacao_id = db.Column(db.Integer, db.ForeignKey('comunicacao_obra.id'))
    comunicacao = db.relationship("ComunicacaoObra", backref="vistoria", uselist=False)

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


