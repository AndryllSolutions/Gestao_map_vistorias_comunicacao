from flask import Blueprint, request, jsonify

from ..models import db, Imovel
from app import db

imoveis_bp = Blueprint('imoveis', __name__)


@imoveis_bp.route('/', methods=['GET'])
def listar_imoveis():
    imoveis = Imovel.query.all()
    lista = []
    for imovel in imoveis:
        lista.append({
            'id': imovel.id,
            'endereco': imovel.endereco,
            'descricao': imovel.descricao,
            'preco': imovel.preco,
        })
    return jsonify(lista)


@imoveis_bp.route('/', methods=['POST'])
def criar_imovel():
    data = request.json
    endereco = data.get('endereco')
    descricao = data.get('descricao')
    preco = data.get('preco')

    if not endereco or preco is None:
        return jsonify({'mensagem': 'Endereço e preço são obrigatórios'}), 400

    imovel = Imovel(endereco=endereco, descricao=descricao, preco=preco)
    db.session.add(imovel)
    db.session.commit()
    return jsonify({'mensagem': 'Imóvel criado com sucesso'}), 201


@imoveis_bp.route('/<int:id>', methods=['PUT'])
def atualizar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    data = request.json
    imovel.endereco = data.get('endereco', imovel.endereco)
    imovel.descricao = data.get('descricao', imovel.descricao)
    imovel.preco = data.get('preco', imovel.preco)
    db.session.commit()
    return jsonify({'mensagem': 'Imóvel atualizado com sucesso'})


@imoveis_bp.route('/<int:id>', methods=['DELETE'])
def deletar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    db.session.delete(imovel)
    db.session.commit()
    return jsonify({'mensagem': 'Imóvel deletado com sucesso'})
