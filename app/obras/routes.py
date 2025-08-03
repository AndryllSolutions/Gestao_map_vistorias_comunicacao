from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)

from ..models import db, ComunicacaoObra, Obra, User
from ..utils import registrar_acao

obras_bp = Blueprint('obras', __name__)


@obras_bp.route('/comunicacoes/<int:id>/editar', methods=['GET', 'POST'])
def editar_comunicacao(id):
    comunicacao = ComunicacaoObra.query.get_or_404(id)

    if request.method == 'POST':
        comunicacao.nome = request.form.get('nome')
        comunicacao.cpf = request.form.get('cpf')
        comunicacao.endereco = request.form.get('endereco')
        comunicacao.telefone = request.form.get('telefone')
        comunicacao.comunicado = request.form.get('comunicado')
        comunicacao.economia = request.form.get('economia')
        comunicacao.assinatura = request.form.get('assinatura')
        tipo_imovel_list = request.form.getlist('tipo_imovel')
        comunicacao.tipo_imovel = ','.join(tipo_imovel_list)

        db.session.commit()
        flash('Comunicação atualizada com sucesso!', 'success')
        return redirect(url_for('obras.listar_comunicacoes'))

    return render_template('editar_comunicacao.html', comunicacao=comunicacao)


@obras_bp.route('/comunicacao', methods=['GET', 'POST'])
def formulario_comunicacao():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')
        comunicado = request.form.get('comunicado')
        economia = request.form.get('economia')
        assinatura = request.form.get('assinatura')
        tipo_imovel = request.form.getlist('tipo_imovel')

        novo = ComunicacaoObra(
            nome=nome,
            cpf=cpf,
            endereco=endereco,
            telefone=telefone,
            comunicado=comunicado,
            economia=economia,
            assinatura=assinatura,
            tipo_imovel=','.join(tipo_imovel),
        )

        db.session.add(novo)
        db.session.commit()

        return redirect(url_for('obras.formulario_comunicacao'))

    return render_template('comunicacao_form.html')


@obras_bp.route('/comunicacoes', methods=['GET'])
def listar_comunicacoes():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])

    if user.cargo == 'admin':
        obras = Obra.query.order_by(Obra.nome).all()
    else:
        obras = Obra.query.filter_by(id=user.obra_id).all()

    return render_template('comunicacoes_dashboard.html', obras=obras)


@obras_bp.route('/comunicacao/passo1', methods=['GET', 'POST'])
def comunicacao_passo1():
    obras = Obra.query.all()

    if request.method == 'POST':
        session['nome'] = request.form.get('nome')
        session['cpf'] = request.form.get('cpf')
        session['endereco'] = request.form.get('endereco')
        session['telefone'] = request.form.get('telefone')
        session['obra_id'] = request.form.get('obra_id')
        return redirect(url_for('obras.comunicacao_passo2'))

    return render_template('etapa1.html', obras=obras)


@obras_bp.route('/comunicacao/passo2', methods=['GET', 'POST'])
def comunicacao_passo2():
    if request.method == 'POST':
        session['comunicado'] = request.form.get('comunicado')
        return redirect(url_for('obras.comunicacao_passo3'))
    return render_template('etapa2.html')


@obras_bp.route('/comunicacao/passo3', methods=['GET', 'POST'])
def comunicacao_passo3():
    if request.method == 'POST':
        economia = request.form.get('economia')
        assinatura = request.form.get('assinatura')
        tipos = request.form.getlist('tipo_imovel')

        novo = ComunicacaoObra(
            nome=session.get('nome'),
            cpf=session.get('cpf'),
            endereco=session.get('endereco'),
            telefone=session.get('telefone'),
            comunicado=session.get('comunicado'),
            economia=economia,
            assinatura=assinatura,
            tipo_imovel=','.join(tipos),
            obra_id=int(session.get('obra_id')) if session.get('obra_id') else None,
        )

        db.session.add(novo)
        db.session.commit()

        if 'user_id' in session and session.get('cargo') == 'admin':
            registrar_acao(
                usuario_id=session['user_id'],
                tipo_acao='criação',
                entidade='Comunicação',
                entidade_id=novo.id,
                observacao=f'Comunicação registrada para {novo.nome}, endereço: {novo.endereco}',
            )

        for chave in ['nome', 'cpf', 'endereco', 'telefone', 'comunicado', 'obra_id']:
            session.pop(chave, None)

        if 'user_id' in session and session.get('cargo') == 'admin':
            return redirect(url_for('obras.listar_comunicacoes'))
        else:
            return render_template('comunicacao_sucesso.html')

    return render_template('etapa3.html')


@obras_bp.route('/comunicacao/excluir/<int:id>', methods=['POST'])
def excluir_comunicacao(id):
    if session.get('cargo') != 'admin':
        return 'Acesso negado', 403

    comunicacao = ComunicacaoObra.query.get_or_404(id)
    db.session.delete(comunicacao)
    db.session.commit()

    registrar_acao(
        usuario_id=session['user_id'],
        tipo_acao='exclusão',
        entidade='Comunicação',
        entidade_id=id,
        observacao=f'Registro excluído: {comunicacao.nome}',
    )

    flash('🗑️ Registro excluído com sucesso!', 'danger')
    return redirect(url_for('obras.listar_comunicacoes'))


@obras_bp.route('/api/comunicacoes/dados')
def comunicacoes_dados():
    registros = ComunicacaoObra.query.all()

    total = len(registros)

    por_endereco = {}
    por_comunicado = {}
    por_tipo = {}

    for r in registros:
        por_endereco[r.endereco] = por_endereco.get(r.endereco, 0) + 1
        por_comunicado[r.comunicado] = por_comunicado.get(r.comunicado, 0) + 1
        if r.tipo_imovel:
            tipos = r.tipo_imovel.split(',')
            for tipo in tipos:
                tipo = tipo.strip()
                por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    return jsonify({
        'total': total,
        'por_endereco': por_endereco,
        'por_comunicado': por_comunicado,
        'por_tipo': por_tipo,
    })
