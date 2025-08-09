from datetime import datetime

from flask import Blueprint, request, jsonify, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import db, User, Obra
from ..utils import registrar_acao
from app import db
from app.models import User, HistoricoAcao
import uuid
import os
import requests
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    if 'usuario' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['usuario']).first()
    if user.cargo != 'admin':
        return 'Acesso negado', 403

    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")
    cargo = request.form.get("cargo")
    obra_id = request.form.get("obra_id") or None


    if not email or not senha:
        flash('E-mail e senha são obrigatórios.', 'warning')
        return redirect(url_for('auth.gerenciar_usuarios'))

    if User.query.filter_by(email=email).first():
        flash('Já existe um usuário com esse e-mail.', 'danger')
        return redirect(url_for('auth.gerenciar_usuarios'))

    hashed_senha = generate_password_hash(senha)
    novo_usuario = User(
        nome=nome,
        email=email,
        password=generate_password_hash(senha),
        cargo=cargo,
        obra_id=obra_id
)

    db.session.add(novo_usuario)
    db.session.commit()
    flash('Usuário criado com sucesso!', 'success')
    return redirect(url_for('auth.gerenciar_usuarios'))


@auth_bp.route('/redefinir-senha', methods=['GET', 'POST'])
def form_redefinir_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        nova_senha = request.form.get('nova_senha')

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(nova_senha)
            db.session.commit()
            flash('Senha atualizada com sucesso!', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('E-mail não encontrado.', 'danger')

    return render_template('auth/redefinir_senha.html')

@auth_bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
def editar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    obras = Obra.query.all()

    if request.method == 'POST':
        usuario.nome = request.form['nome']  # 👈 Corrigido aqui
        email = request.form.get('email').strip()
        senha = request.form.get('senha')
        cargo = request.form.get('cargo')
        obra_id = request.form.get('obra_id') or None
        usuario.rg = request.form.get('rg')


        alterado = False

        if usuario.email != email:
            usuario.email = email
            alterado = True

        if senha:
            usuario.password = generate_password_hash(senha)
            alterado = True

        if usuario.cargo != cargo:
            usuario.cargo = cargo
            alterado = True

        if str(usuario.obra_id) != str(obra_id):
            usuario.obra_id = int(obra_id) if obra_id else None
            alterado = True

        if alterado:
            db.session.commit()
            flash('Usuário editado com sucesso!', 'success')
        else:
            flash('Nenhuma alteração foi feita.', 'info')

        return redirect(url_for('auth.gerenciar_usuarios'))

    return render_template('usuarios/editar_usuario.html', usuario=usuario, obras=obras)


@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Sessão expirada'}), 401
        else:
            return redirect(url_for('auth.login_form'))  # Redireciona para index.html

    user = User.query.get(session['user_id'])

    obra_nome = user.obra.nome if user.obra else 'Não vinculada'

    return render_template(
        'auth/dashboard.html',
        usuario=user.email,
        cargo=user.cargo,
        ano=datetime.now().year,
        obra_nome=obra_nome,
    )





@auth_bp.route('/cadastro', methods=['POST'])
def cadastrar():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({'mensagem': 'Preencha todos os campos'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'mensagem': 'E-mail já cadastrado'}), 409

    hashed = generate_password_hash(senha)
    novo_usuario = User(email=email, password=hashed)
    db.session.add(novo_usuario)
    db.session.commit()

    if 'user_id' in session:
        registrar_acao(
            usuario_id=session['user_id'],
            tipo_acao='criação',
            entidade='Usuário',
            entidade_id=novo_usuario.id,
            observacao=f'Usuário criado: {novo_usuario.email}'
        )

    return jsonify({'mensagem': 'Usuário cadastrado com sucesso'}), 201


@auth_bp.route('/cadastro', methods=['GET'])
def cadastro_form():
    return render_template('auth/cadastro.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session.permanent = True  # <- ESSENCIAL para usar o tempo de expiração configurado
        session['user_id'] = user.id
        session['usuario'] = user.email
        session['cargo'] = user.cargo
        return jsonify({'redirect': '/dashboard'})

    return jsonify({'error': 'Login inválido'}), 401
#return render_template('index.html')  # já é o seu template de login
@auth_bp.route('/login', methods=['GET'])
def login_form():
    return render_template('index.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))


@auth_bp.route('/gerenciar-usuarios', methods=['GET', 'POST'])
def gerenciar_usuarios():
    if 'usuario' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['usuario']).first()
    if user.cargo != 'admin':
        return 'Acesso negado', 403

    if request.method == 'POST':
        usuario_id = request.form.get('usuario_id')
        novo_cargo = request.form.get('novo_cargo')
        obra_id = request.form.get('obra_id')

        usuario_alvo = User.query.get(usuario_id)
        if usuario_alvo:
            usuario_alvo.cargo = novo_cargo
            usuario_alvo.obra_id = int(obra_id) if obra_id else None
            db.session.commit()

    usuarios = User.query.all()
    obras = Obra.query.all()
    return  render_template('usuarios/gerenciar_usuarios.html', usuarios=usuarios, obras=obras)



@auth_bp.route('/atualizar_cargo/<int:user_id>', methods=['POST'])
def atualizar_cargo(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_logado = User.query.get(session['user_id'])
    if user_logado.cargo != 'admin':
        return 'Acesso negado', 403

    novo_cargo = request.form['novo_cargo']
    usuario = User.query.get(user_id)
    if usuario:
        usuario.cargo = novo_cargo
        db.session.commit()

    registrar_acao(
        usuario_id=user_logado.id,
        tipo_acao='edição',
        entidade='Usuário',
        entidade_id=usuario.id,
        observacao=f"Cargo alterado para '{novo_cargo}' do usuário {usuario.email}"
    )
    return redirect(url_for('auth.gerenciar_usuarios'))


@auth_bp.route('/excluir_usuario/<int:user_id>', methods=['POST'])
def excluir_usuario(user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_logado = User.query.get(session['user_id'])
    if user_logado.cargo != 'admin':
        return 'Acesso negado', 403

    usuario = User.query.get(user_id)
    if usuario and usuario.id != user_logado.id:
        db.session.delete(usuario)
        db.session.commit()

    registrar_acao(
        usuario_id=user_logado.id,
        tipo_acao='exclusão',
        entidade='Usuário',
        entidade_id=usuario.id,
        observacao=f'Usuário excluído: {usuario.email}'
    )

    return redirect(url_for('auth.gerenciar_usuarios'))

@auth_bp.route('/historico')
def historico():
    if session.get('cargo') != 'admin':
        flash('Apenas administradores podem acessar o histórico.', 'danger')
        return redirect(url_for('auth.dashboard'))

    query = HistoricoAcao.query.join(User).order_by(HistoricoAcao.data_hora.desc())

    # Filtros opcionais
    tipo = request.args.get("tipo")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    if tipo:
        query = query.filter(HistoricoAcao.tipo_acao == tipo)
    if inicio:
        query = query.filter(HistoricoAcao.data_hora >= datetime.strptime(inicio, "%Y-%m-%d"))
    if fim:
        query = query.filter(HistoricoAcao.data_hora <= datetime.strptime(fim, "%Y-%m-%d"))

    acoes = query.all()

    return render_template("historico/historico.html", acoes=acoes)


