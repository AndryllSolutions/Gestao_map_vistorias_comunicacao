from flask import Flask, request, jsonify, render_template, redirect, session,url_for
from flask_cors import CORS
from models import db, User, Imovel,ComunicacaoObra
import os
from datetime import datetime
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "Aninha_pitukinha"  # 🔒 use algo mais seguro em produção!
CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Páginas
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect("/")
    usuario = session["usuario"]
    ano_atual = datetime.now().year
    return render_template("dashboard.html", usuario=usuario, ano=ano_atual)



# Cadastro usuário
@app.route("/cadastro", methods=["POST"])
def cadastrar():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"mensagem": "Preencha todos os campos"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"mensagem": "E-mail já cadastrado"}), 409

    novo_usuario = User(email=email, password=senha)
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({"mensagem": "Usuário cadastrado com sucesso"}), 201

@app.route("/cadastro", methods=["GET"])
def cadastro_form():
    return render_template("cadastro.html")


# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"mensagem": "E-mail não cadastrado"}), 404

    if user.password != senha:
        return jsonify({"mensagem": "Senha incorreta"}), 401

    # Salva usuário na sessão
    session["usuario"] = email
    return jsonify({"mensagem": "Login bem-sucedido", "usuario": email}), 200


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))  # substitua "login" pelo nome da sua função de login

# CRUD IMÓVEIS - API REST
@app.route("/imoveis", methods=["GET"])
def listar_imoveis():
    imoveis = Imovel.query.all()
    lista = []
    for imovel in imoveis:
        lista.append({
            "id": imovel.id,
            "endereco": imovel.endereco,
            "descricao": imovel.descricao,
            "preco": imovel.preco
        })
    return jsonify(lista)

@app.route("/imoveis", methods=["POST"])
def criar_imovel():
    data = request.json
    endereco = data.get("endereco")
    descricao = data.get("descricao")
    preco = data.get("preco")

    if not endereco or preco is None:
        return jsonify({"mensagem": "Endereço e preço são obrigatórios"}), 400

    imovel = Imovel(endereco=endereco, descricao=descricao, preco=preco)
    db.session.add(imovel)
    db.session.commit()
    return jsonify({"mensagem": "Imóvel criado com sucesso"}), 201

@app.route("/imoveis/<int:id>", methods=["PUT"])
def atualizar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    data = request.json
    imovel.endereco = data.get("endereco", imovel.endereco)
    imovel.descricao = data.get("descricao", imovel.descricao)
    imovel.preco = data.get("preco", imovel.preco)
    db.session.commit()
    return jsonify({"mensagem": "Imóvel atualizado com sucesso"})

@app.route("/imoveis/<int:id>", methods=["DELETE"])
def deletar_imovel(id):
    imovel = Imovel.query.get_or_404(id)
    db.session.delete(imovel)
    db.session.commit()
    return jsonify({"mensagem": "Imóvel deletado com sucesso"})



@app.route("/comunicacao", methods=["GET", "POST"])
def formulario_comunicacao():
    if request.method == "POST":
        nome = request.form.get("nome")
        cpf = request.form.get("cpf")
        endereco = request.form.get("endereco")
        telefone = request.form.get("telefone")
        comunicado = request.form.get("comunicado")
        economia = request.form.get("economia")
        assinatura = request.form.get("assinatura")
        tipo_imovel = request.form.getlist("tipo_imovel")  # checkbox múltiplo

        novo = ComunicacaoObra(
            nome=nome,
            cpf=cpf,
            endereco=endereco,
            telefone=telefone,
            comunicado=comunicado,
            economia=economia,
            assinatura=assinatura,
            tipo_imovel=",".join(tipo_imovel)
        )

        db.session.add(novo)
        db.session.commit()
        return redirect(url_for("formulario_comunicacao"))

    return render_template("comunicacao_form.html")

@app.route("/comunicacoes", methods=["GET"])
def listar_comunicacoes():
    registros = ComunicacaoObra.query.order_by(ComunicacaoObra.id.desc()).all()
    return render_template("comunicacoes_dashboard.html", registros=registros)

# ETAPA 1 - Dados pessoais
@app.route("/comunicacao/passo1", methods=["GET", "POST"])
def comunicacao_passo1():
    if request.method == "POST":
        session["nome"] = request.form.get("nome")
        session["cpf"] = request.form.get("cpf")
        session["endereco"] = request.form.get("endereco")
        session["telefone"] = request.form.get("telefone")
        return redirect(url_for("comunicacao_passo2"))
    return render_template("etapa1.html")

# ETAPA 2 - Forma de comunicação
@app.route("/comunicacao/passo2", methods=["GET", "POST"])
def comunicacao_passo2():
    if request.method == "POST":
        session["comunicado"] = request.form.get("comunicado")
        return redirect(url_for("comunicacao_passo3"))
    return render_template("etapa2.html")

# ETAPA 3 - Dados técnicos e salvar
@app.route("/comunicacao/passo3", methods=["GET", "POST"])
def comunicacao_passo3():
    if request.method == "POST":
        economia = request.form.get("economia")
        assinatura = request.form.get("assinatura")
        tipos = request.form.getlist("tipo_imovel")

        from models import ComunicacaoObra

        novo = ComunicacaoObra(
            nome=session.get("nome"),
            cpf=session.get("cpf"),
            endereco=session.get("endereco"),
            telefone=session.get("telefone"),
            comunicado=session.get("comunicado"),
            economia=economia,
            assinatura=assinatura,
            tipo_imovel=",".join(tipos)
        )
        db.session.add(novo)
        db.session.commit()
        session.clear()  # limpa os dados após salvar

        return redirect(url_for("listar_comunicacoes"))  # exibe lista final

    return render_template("etapa3.html")


@app.route("/gerenciar-usuarios", methods=["GET", "POST"])
def gerenciar_usuarios():
    if "usuario" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["usuario"]).first()
    if user.cargo != "admin":
        return "Acesso negado", 403

    if request.method == "POST":
        usuario_id = request.form.get("usuario_id")
        novo_cargo = request.form.get("novo_cargo")
        usuario_alvo = User.query.get(usuario_id)
        if usuario_alvo:
            usuario_alvo.cargo = novo_cargo
            db.session.commit()
    usuarios = User.query.all()
    return render_template("gerenciar_usuarios.html", usuarios=usuarios)

@app.route('/atualizar_cargo/<int:user_id>', methods=['POST'])
def atualizar_cargo(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_logado = User.query.get(session['user_id'])
    if user_logado.cargo != 'admin':
        return "Acesso negado", 403

    novo_cargo = request.form['novo_cargo']
    usuario = User.query.get(user_id)
    if usuario:
        usuario.cargo = novo_cargo
        db.session.commit()
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/excluir_usuario/<int:user_id>', methods=['POST'])
def excluir_usuario(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_logado = User.query.get(session['user_id'])
    if user_logado.cargo != 'admin':
        return "Acesso negado", 403

    usuario = User.query.get(user_id)
    if usuario and usuario.id != user_logado.id:  # Impede excluir a si mesmo
        db.session.delete(usuario)
        db.session.commit()

    return redirect(url_for('gerenciar_usuarios'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Banco criado/atualizado!")
    app.run(host="0.0.0.0", port=5000)
