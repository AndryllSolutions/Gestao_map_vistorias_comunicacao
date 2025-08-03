from flask import Flask, request, jsonify, render_template, redirect, session,url_for,send_file,flash
from flask_cors import CORS
from models import db, User, Imovel,ComunicacaoObra,VistoriaImovel,AgendamentoVistoria,HistoricoAcao,Obra,FotoVistoria
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask_migrate import Migrate
from textwrap import wrap
from sqlalchemy import and_
import pandas as pd
from fpdf import FPDF
from flask_migrate import Migrate
from datetime import timedelta,datetime
import requests
from werkzeug.utils import secure_filename
import ftplib
from reportlab.lib.colors import black
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from sqlalchemy.orm import joinedload

app = Flask(__name__, static_folder='static', template_folder='templates')
app.jinja_env.globals['now'] = datetime.now
app.secret_key = "Aninha_pitukinha"  # 🔒 use algo mais seguro em produção!
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Ngrok é HTTPS
CORS(app)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()
    #if not User.query.filter_by(email="admin@obra.com").first():
      #  admin = User(email="admin@obra.com", password="admin123", cargo="admin")
       # db.session.add(admin)
       # db.session.commit()
       # print("✅ Admin padrão criado: admin@obra.com / admin123")

# Páginas
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/criar_usuario', methods=["POST"])
def criar_usuario():
    if "usuario" not in session:
        return redirect("/login")

    user = User.query.filter_by(email=session["usuario"]).first()
    if user.cargo != "admin":
        return "Acesso negado", 403

    email = request.form.get("email")
    senha = request.form.get("senha")
    cargo = request.form.get("cargo")
    obra_id = request.form.get("obra_id") or None

    if not email or not senha:
        flash("E-mail e senha são obrigatórios.", "warning")
        return redirect(url_for("gerenciar_usuarios"))

    # Verifica se já existe o e-mail
    if User.query.filter_by(email=email).first():
        flash("Já existe um usuário com esse e-mail.", "danger")
        return redirect(url_for("gerenciar_usuarios"))

    hashed_senha = generate_password_hash(senha)
    novo_usuario = User(
        email=email,
        password=hashed_senha,
        cargo=cargo,
        obra_id=int(obra_id) if obra_id else None
    )

    db.session.add(novo_usuario)
    db.session.commit()
    flash("Usuário criado com sucesso!", "success")
    return redirect(url_for("gerenciar_usuarios"))
@app.route("/redefinir-senha", methods=["GET", "POST"])
def form_redefinir_senha():
    if request.method == "POST":
        email = request.form.get("email")
        nova_senha = request.form.get("nova_senha")

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(nova_senha)
            db.session.commit()
            flash("Senha atualizada com sucesso!", "success")
            return redirect(url_for("index"))
        else:
            flash("E-mail não encontrado.", "danger")

    return render_template("redefinir_senha.html")

@app.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
def editar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    obras = Obra.query.all()

    if request.method == "POST":
        email = request.form.get("email").strip()
        senha = request.form.get("senha")
        cargo = request.form.get("cargo")
        obra_id = request.form.get("obra_id") or None

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
            flash("Usuário editado com sucesso!", "success")
        else:
            flash("Nenhuma alteração foi feita.", "info")

        return redirect(url_for("gerenciar_usuarios"))

    return render_template("editar_usuario.html", usuario=usuario, obras=obras)




@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", usuario=user.email, cargo=user.cargo, ano=datetime.now().year)




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

    hashed = generate_password_hash(senha)
    novo_usuario = User(email=email, password=hashed)
    db.session.add(novo_usuario)
    db.session.commit()

    # Registrar histórico se for admin criando
    if "user_id" in session:
        registrar_acao(
            usuario_id=session["user_id"],
            tipo_acao="criação",
            entidade="Usuário",
            entidade_id=novo_usuario.id,
            observacao=f"Usuário criado: {novo_usuario.email}"
        )

    return jsonify({"mensagem": "Usuário cadastrado com sucesso"}), 201



@app.route("/cadastro", methods=["GET"])
def cadastro_form():
    return render_template("cadastro.html")


# Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        session["usuario"] = user.email
        session["cargo"] = user.cargo
        return jsonify({"redirect": "/dashboard"})
    
    return jsonify({"error": "Login inválido"}), 401



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


@app.route("/comunicacoes/<int:id>/editar", methods=["GET", "POST"])
def editar_comunicacao(id):
    comunicacao = ComunicacaoObra.query.get_or_404(id)

    if request.method == "POST":
        comunicacao.nome = request.form.get("nome")
        comunicacao.cpf = request.form.get("cpf")
        comunicacao.endereco = request.form.get("endereco")
        comunicacao.telefone = request.form.get("telefone")
        comunicacao.comunicado = request.form.get("comunicado")
        comunicacao.economia = request.form.get("economia")
        comunicacao.assinatura = request.form.get("assinatura")

        # ✅ Captura múltiplos checkboxes como string separada por vírgula
        tipo_imovel_list = request.form.getlist("tipo_imovel")
        comunicacao.tipo_imovel = ",".join(tipo_imovel_list)

        db.session.commit()
        flash("Comunicação atualizada com sucesso!", "success")
        return redirect(url_for("listar_comunicacoes"))

    return render_template("editar_comunicacao.html", comunicacao=comunicacao)

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

#@app.route("/comunicacoes", methods=["GET"])
#def listar_comunicacoes():
   # if "user_id" not in session:
     #   return redirect(url_for("login"))
#
   # registros = ComunicacaoObra.query.order_by(ComunicacaoObra.id.desc()).all()
   # return render_template("comunicacoes_dashboard.html", registros=registros)


@app.route("/comunicacoes", methods=["GET"])
def listar_comunicacoes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if user.cargo == "admin":
        obras = Obra.query.order_by(Obra.nome).all()
    else:
        obras = Obra.query.filter_by(id=user.obra_id).all()

    return render_template("comunicacoes_dashboard.html", obras=obras)


# ETAPA 1 - Dados pessoais
@app.route("/comunicacao/passo1", methods=["GET", "POST"])
def comunicacao_passo1():
    obras = Obra.query.all()

    if request.method == "POST":
        session["nome"] = request.form.get("nome")
        session["cpf"] = request.form.get("cpf")
        session["endereco"] = request.form.get("endereco")
        session["telefone"] = request.form.get("telefone")
        session["obra_id"] = request.form.get("obra_id")  # <- ESSA LINHA É NOVA!
        return redirect(url_for("comunicacao_passo2"))

    return render_template("etapa1.html", obras=obras)


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

        novo = ComunicacaoObra(
            nome=session.get("nome"),
            cpf=session.get("cpf"),
            endereco=session.get("endereco"),
            telefone=session.get("telefone"),
            comunicado=session.get("comunicado"),
            economia=economia,
            assinatura=assinatura,
            tipo_imovel=",".join(tipos),
            obra_id=int(session.get("obra_id")) if session.get("obra_id") else None  # <- aqui é o ponto-chave
        )


        db.session.add(novo)
        db.session.commit()

        # Registra no histórico se admin
        if "user_id" in session and session.get("cargo") == "admin":
            registrar_acao(
                usuario_id=session["user_id"],
                tipo_acao="criação",
                entidade="Comunicação",
                entidade_id=novo.id,
                observacao=f"Comunicação registrada para {novo.nome}, endereço: {novo.endereco}"
            )

        # Limpa apenas os dados temporários
        for chave in ["nome", "cpf", "endereco", "telefone", "comunicado", "obra_id"]:
             session.pop(chave, None)


        if "user_id" in session and session.get("cargo") == "admin":
            return redirect(url_for("listar_comunicacoes"))
        else:
            return render_template("comunicacao_sucesso.html")

    return render_template("etapa3.html")




@app.route("/comunicacao/excluir/<int:id>", methods=["POST"])
def excluir_comunicacao(id):
    if session.get("cargo") != "admin":
        return "Acesso negado", 403

    comunicacao = ComunicacaoObra.query.get_or_404(id)
    db.session.delete(comunicacao)
    db.session.commit()

    registrar_acao(
        usuario_id=session["user_id"],
        tipo_acao="exclusão",
        entidade="Comunicação",
        entidade_id=id,
        observacao=f"Registro excluído: {comunicacao.nome}"
    )

    flash("🗑️ Registro excluído com sucesso!", "danger")
    return redirect(url_for("listar_comunicacoes"))


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
        obra_id = request.form.get("obra_id")  # <- NOVO

        usuario_alvo = User.query.get(usuario_id)
        if usuario_alvo:
            usuario_alvo.cargo = novo_cargo
            usuario_alvo.obra_id = int(obra_id) if obra_id else None  # <- NOVO
            db.session.commit()

    usuarios = User.query.all()
    obras = Obra.query.all()  # <- NOVO
    return render_template("gerenciar_usuarios.html", usuarios=usuarios, obras=obras)  # <- NOVO


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

    registrar_acao(
    usuario_id=user_logado.id,
    tipo_acao="edição",
    entidade="Usuário",
    entidade_id=usuario.id,
    observacao=f"Cargo alterado para '{novo_cargo}' do usuário {usuario.email}"
)
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

    registrar_acao(
    usuario_id=user_logado.id,
    tipo_acao="exclusão",
    entidade="Usuário",
    entidade_id=usuario.id,
    observacao=f"Usuário excluído: {usuario.email}"
)

    return redirect(url_for('gerenciar_usuarios'))



@app.route("/api/comunicacoes/dados")
def comunicacoes_dados():
    registros = ComunicacaoObra.query.all()

    total = len(registros)

    por_endereco = {}
    por_comunicado = {}
    por_tipo = {}

    for r in registros:
        # Endereço
        por_endereco[r.endereco] = por_endereco.get(r.endereco, 0) + 1

        # Comunicado
        por_comunicado[r.comunicado] = por_comunicado.get(r.comunicado, 0) + 1

        # Tipo de imóvel (pode ter vários por registro)
        if r.tipo_imovel:
            tipos = r.tipo_imovel.split(",")
            for tipo in tipos:
                tipo = tipo.strip()
                por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    return jsonify({
        "total": total,
        "por_endereco": por_endereco,
        "por_comunicado": por_comunicado,
        "por_tipo": por_tipo
    })

@app.route("/dashboard_power_bi")
def dashboard_power_bi():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    return render_template("dashboard_power_bi.html", usuario=user.email, cargo=user.cargo)

@app.route("/vistoria", methods=["GET", "POST"])
def vistoria():
    if request.method == "POST":
        obra_id = request.form.get("obra_id")
        data_1 = datetime.strptime(request.form.get("data_1"), "%Y-%m-%d").date()
        data_2 = datetime.strptime(request.form.get("data_2"), "%Y-%m-%d").date() if request.form.get("data_2") else None
        data_3 = datetime.strptime(request.form.get("data_3"), "%Y-%m-%d").date() if request.form.get("data_3") else None
        hora_1 = datetime.strptime(request.form.get("hora_1"), "%H:%M").time()
        hora_2 = datetime.strptime(request.form.get("hora_2"), "%H:%M").time() if request.form.get("hora_2") else None
        hora_3 = datetime.strptime(request.form.get("hora_3"), "%H:%M").time() if request.form.get("hora_3") else None

        nome_responsavel = request.form.get("nome_responsavel")
        cpf_responsavel = request.form.get("cpf_responsavel")
        tipo_vinculo = request.form.get("tipo_vinculo")

        municipio = request.form.get("municipio")
        bairro = request.form.get("bairro")
        rua = request.form.get("rua")
        numero = request.form.get("numero")
        complemento = request.form.get("complemento")
        celular = request.form.get("celular")

        tipo_imovel = request.form.get("tipo_imovel")
        soleira = request.form.get("soleira")
        calcada_lista = request.form.getlist("calcada")
        calcada = ", ".join(calcada_lista)
        observacoes = request.form.get("observacoes")

        nova = VistoriaImovel(
            data_1=data_1, hora_1=hora_1,
            data_2=data_2, hora_2=hora_2,
            data_3=data_3, hora_3=hora_3,
            nome_responsavel=nome_responsavel,
            cpf_responsavel=cpf_responsavel,
            tipo_vinculo=tipo_vinculo,
            municipio=municipio, bairro=bairro, rua=rua, numero=numero,
            complemento=complemento, celular=celular,
            tipo_imovel=tipo_imovel, soleira=soleira,
            calcada=calcada, observacoes=observacoes,
            obra_id=obra_id if obra_id else None
        )

        db.session.add(nova)
        db.session.commit()  # Commit necessário antes de salvar fotos (para ter ID)

        # 📸 Upload das fotos
        fotos = request.files.getlist("fotos[]")
        descricoes = request.form.getlist("descricao_fotos[]")
        api_key = "7fc78fa7-ff70-4921-bcc75dd59e58-588a-4188"

        for i, foto in enumerate(fotos):
            if foto and foto.filename:
                nome = secure_filename(f"vistoria_{nova.id}_{i}_{foto.filename}")
                temp_path = os.path.join("temp", nome)
                os.makedirs("temp", exist_ok=True)  # ← Adicione esta linha aqui

                foto.save(temp_path)

                url = upload_bunny(nome, temp_path, api_key)
                os.remove(temp_path)

                if url:
                    nova_foto = FotoVistoria(
                        url=url,
                        descricao=descricoes[i] if i < len(descricoes) else "",
                        vistoria_id=nova.id
                    )
                    db.session.add(nova_foto)

        db.session.commit()

        # Registrar histórico da ação
        if "user_id" in session:
            registrar_acao(
                usuario_id=session["user_id"],
                tipo_acao="criação",
                entidade="Vistoria",
                entidade_id=nova.id,
                observacao=f"Vistoria criada no endereço {nova.rua}, {nova.bairro}"
            )

        flash("✅ Vistoria registrada com sucesso!")
        return redirect(url_for("vistoria"))

    obras = Obra.query.all()
    return render_template("vistoria_form.html", obras=obras)

@app.route("/vistorias")
def listar_vistorias():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    usuario = User.query.get(session["user_id"])
    vistorias = VistoriaImovel.query.order_by(VistoriaImovel.data_1.desc()).all()
   

    return render_template("vistorias_dashboard.html", vistorias=vistorias, cargo=usuario.cargo)



@app.route("/vistoria/laudo/<int:id>")
def gerar_laudo_vistoria(id):
    LOGO_PATH = os.path.join("static", "logo.png")
    vistoria = VistoriaImovel.query.get_or_404(id)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    y = 800

    def draw_wrapped_text(texto, x, y, width=100, line_height=15, font="Helvetica", font_size=11):
        c.setFont(font, font_size)
        for linha in wrap(texto, width=width):
            c.drawString(x, y, linha)
            y -= line_height
        return y

    # Logo
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(logo, 50, altura - 60, width=100, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Erro ao carregar o logo:", e)

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "LAUDO DA VISTORIA CAUTELAR")
    y -= 40

    # Dados principais
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Data da Vistoria: {vistoria.data_1 or 'N/A'} {vistoria.hora_1 or ''}")
    y -= 20
    c.drawString(50, y, f"Responsável: {vistoria.nome_responsavel or 'N/A'} - CPF: {vistoria.cpf_responsavel or 'N/A'}")
    y -= 20
    c.drawString(50, y, f"Vínculo: {vistoria.tipo_vinculo or 'N/A'}")
    y -= 20
    c.drawString(50, y, f"Endereço: {vistoria.rua}, {vistoria.numero} - {vistoria.bairro}, {vistoria.municipio}")
    y -= 20
    c.drawString(50, y, f"Tipo de Imóvel: {vistoria.tipo_imovel}")
    y -= 20
    c.drawString(50, y, f"Soleira: {vistoria.soleira}")
    y -= 20
    c.drawString(50, y, f"Calçada: {vistoria.calcada}")
    y -= 20
    obra_nome = vistoria.obra.nome if vistoria.obra else "Obra não especificada"
    c.drawString(50, y, f"Obra: {obra_nome}")
    y -= 30

    # Normas e LGPD
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Norma Técnica")
    y -= 20
    y = draw_wrapped_text(
        "ABNT NBR 12722:1992 - Discriminação de serviços para construção de edifícios.\n"
        "A vistoria resguarda os interesses das partes envolvidas e do público em geral, "
        "devendo ser realizada por profissional especializado, incluindo planta de localização, "
        "relatório descritivo e registros fotográficos.",
        50, y
    )
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Informações Legais - LGPD")
    y -= 20
    y = draw_wrapped_text(
        "Em conformidade com a Lei Geral de Proteção de Dados (LGPD), realizamos a vistoria cautelar no imóvel, "
        "coletando apenas os dados necessários. As informações serão utilizadas exclusivamente para os fins da vistoria "
        "e não serão compartilhadas sem consentimento, salvo por exigência legal.",
        50, y
    )
    y -= 10

    # Observações
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Observações Finais:")
    y -= 20
    observacoes = vistoria.observacoes or "Sem observações."
    y = draw_wrapped_text(observacoes, 50, y)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Ciência do Morador quanto à Vistoria")
    y -= 20
    ciencia_texto = (
        f"Eu, {vistoria.nome_responsavel or '________________'}, portador do CPF {vistoria.cpf_responsavel or '________________'}, "
        "declaro que forneci de livre e espontânea vontade todas as informações referentes ao meu imóvel e estou ciente "
        "das fotografias e observações registradas durante a vistoria. Confirmo que estou de acordo com o conteúdo deste laudo."
    )
    y = draw_wrapped_text(ciencia_texto, 50, y)

    y -= 40
    c.drawString(50, y, "________________________________________")
    y -= 15
    c.drawString(50, y, "Assinatura do Responsável")

    # Fotos
    fotos = vistoria.fotos
    if fotos:
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura / 2, altura - 50, "REGISTRO FOTOGRÁFICO")

        img_width = 220
        img_height = 140
        cols = 2
        rows = 3
        space_x = 40
        space_y = 90
        margin_x = 50
        TITULO_Y = altura - 50
        margin_top = TITULO_Y - 160

        x_positions = [margin_x + (img_width + space_x) * col for col in range(cols)]
        y_positions = [margin_top - (img_height + space_y) * row for row in range(rows)]

        for index, foto in enumerate(fotos):
            col = index % cols
            row = (index // cols) % rows

            if index % 6 == 0 and index > 0:
                c.showPage()
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(largura / 2, altura - 50, "REGISTRO FOTOGRÁFICO")

            x = x_positions[col]
            y = y_positions[row]

            try:
                img = ImageReader(foto.url)
                c.drawImage(img, x, y, width=img_width, height=img_height, preserveAspectRatio=True, anchor='n')
                c.setStrokeColor(black)
                c.rect(x, y, img_width, img_height, fill=0)

                legenda = foto.descricao or "Sem título"
                c.setFont("Helvetica", 10)
                c.drawCentredString(x + img_width / 2, y - 14, f"Foto {index + 1}: {legenda}")

                if foto.data_envio:
                    data_formatada = foto.data_envio.strftime("%d/%m/%Y %H:%M")
                    c.setFont("Helvetica-Oblique", 8)
                    c.drawCentredString(x + img_width / 2, y - 28, f"Enviada em {data_formatada}")

            except Exception as e:
                print("Erro ao carregar imagem no PDF:", e)

    # Finaliza o PDF
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"laudo_vistoria_{id}.pdf",
        mimetype='application/pdf'
    )

@app.route("/agendamentos")
def listar_agendamentos():
    nome = request.args.get("nome", "")
    data = request.args.get("data", "")

    query = AgendamentoVistoria.query

    if nome:
        query = query.filter(AgendamentoVistoria.nome_morador.ilike(f"%{nome}%"))
    if data:
        try:
            data_obj = datetime.strptime(data, "%Y-%m-%d").date()
            query = query.filter(AgendamentoVistoria.data_agendada == data_obj)
        except ValueError:
            flash("⚠️ Data inválida", "warning")

    agendamentos = query.order_by(AgendamentoVistoria.data_agendada.desc()).all()
    return render_template("agendamentos.html", agendamentos=agendamentos)



@app.route("/agendar", methods=["GET", "POST"])
def agendar_vistoria():
    if request.method == "POST":
        try:
            data_agendada = datetime.strptime(request.form["data_agendada"], "%Y-%m-%d").date()
            hora_agendada = datetime.strptime(request.form["hora_agendada"], "%H:%M").time()
            obra_id = request.form.get("obra_id")
            obra_id = int(obra_id) if obra_id else None


            novo_agendamento = AgendamentoVistoria(
                nome_morador=request.form["nome_morador"],
                celular=request.form["celular"],
                endereco=request.form["endereco"],
                bairro=request.form["bairro"],
                cidade=request.form["cidade"],
                data_agendada=data_agendada,
                hora_agendada=hora_agendada,
                observacoes=request.form["observacoes"],
                obra_id=obra_id if obra_id else None
            )
            db.session.add(novo_agendamento)
            db.session.commit()

            registrar_acao(
                usuario_id=session["user_id"],
                tipo_acao="criação",
                entidade="Agendamento",
                entidade_id=novo_agendamento.id,
                observacao=f"Agendamento criado: {novo_agendamento.nome_morador}, {novo_agendamento.endereco}"
            )


            flash("✅ Agendamento realizado com sucesso!", "success")
            return redirect(url_for("agendar_vistoria"))

        except Exception as e:
            print(f"Erro no agendamento: {e}")
            flash("❌ Erro ao tentar salvar o agendamento.", "danger")
    obras = Obra.query.all()

    return render_template("agendar.html", obras=obras)


@app.route("/agendamento/editar/<int:agendamento_id>", methods=["GET", "POST"])
def editar_agendamento(agendamento_id):
    agendamento = AgendamentoVistoria.query.get_or_404(agendamento_id)

    if request.method == "POST":
        agendamento.nome_morador = request.form["nome_morador"]
        agendamento.celular = request.form["celular"]
        agendamento.endereco = request.form["endereco"]
        agendamento.bairro = request.form["bairro"]
        agendamento.cidade = request.form["cidade"]
        agendamento.data_agendada = datetime.strptime(request.form["data_agendada"], "%Y-%m-%d").date()
        agendamento.hora_agendada = datetime.strptime(request.form["hora_agendada"], "%H:%M").time()
        agendamento.observacoes = request.form["observacoes"]

        db.session.commit()

        if "user_id" in session:
            registrar_acao(
                usuario_id=session["user_id"],
                tipo_acao="edição",
                entidade="Agendamento",
                entidade_id=agendamento.id,
                observacao=f"Edição agendamento de {agendamento.nome_morador} em {agendamento.data_agendada}"
            )

        flash("✏️ Agendamento atualizado com sucesso!", "success")
        return redirect(url_for("listar_agendamentos"))

    return render_template("editar_agendamento.html", agendamento=agendamento)

@app.route("/agendamento/excluir/<int:agendamento_id>")
def excluir_agendamento(agendamento_id):
    agendamento = AgendamentoVistoria.query.get_or_404(agendamento_id)

    if "user_id" in session:
        registrar_acao(
            usuario_id=session["user_id"],
            tipo_acao="exclusão",
            entidade="Agendamento",
            entidade_id=agendamento.id,
            observacao=f"Agendamento excluído: {agendamento.nome_morador}, {agendamento.endereco}"
        )

    db.session.delete(agendamento)
    db.session.commit()
    flash("🗑️ Agendamento excluído com sucesso!", "danger")
    return redirect(url_for("listar_agendamentos"))




@app.route("/exportar/vistorias/excel")
def exportar_vistorias_excel():
    vistorias = Vistoria.query.all()
    dados = [{
        "ID": v.id,
        "Município": v.municipio,
        "Bairro": v.bairro,
        "Rua": v.rua,
        "Data": v.data_1.strftime("%d/%m/%Y"),
        "Hora": v.hora_1,
        "Tipo": v.tipo_imovel,
        "Observações": v.observacoes
    } for v in vistorias]
    df = pd.DataFrame(dados)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="vistorias.xlsx", as_attachment=True)

@app.route("/exportar/vistorias/pdf")
def exportar_vistorias_pdf():
    vistorias = Vistoria.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Vistorias", ln=True, align="C")
    for v in vistorias:
        pdf.cell(200, 10, txt=f"ID {v.id} - {v.municipio}, {v.bairro}, {v.rua} - {v.data_1.strftime('%d/%m/%Y')}", ln=True)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="vistorias.pdf", as_attachment=True)


@app.route("/vistoria/editar/<int:id>", methods=["GET", "POST"])
def editar_vistoria(id):
    vistoria = VistoriaImovel.query.get_or_404(id)

    if request.method == "POST":
        # Atualiza os campos principais da vistoria
        vistoria.municipio = request.form.get("municipio")
        vistoria.bairro = request.form.get("bairro")
        vistoria.rua = request.form.get("rua")
        vistoria.data_1 = datetime.strptime(request.form.get("data_1"), "%Y-%m-%d").date()
        vistoria.hora_1 = datetime.strptime(request.form.get("hora_1"), "%H:%M").time()
        vistoria.tipo_imovel = request.form.get("tipo_imovel")
        vistoria.observacoes = request.form.get("observacoes")

        db.session.commit()  # commit para garantir que o ID existe para nomear as fotos

        # Upload das fotos
        fotos = request.files.getlist("fotos[]")
        descricoes = request.form.getlist("descricao_fotos[]")
        api_key = "7fc78fa7-ff70-4921-bcc75dd59e58-588a-4188"  # idealmente use .env

        for i, foto in enumerate(fotos):
            if foto and descricoes[i].strip():
                nome = secure_filename(f"vistoria_{vistoria.id}_{i}_{foto.filename}")
                temp_path = os.path.join("temp", nome)
                foto.save(temp_path)

                url = upload_bunny(nome, temp_path, api_key)
                os.remove(temp_path)

                if url:
                    nova_foto = FotoVistoria(
                        url=url,
                        descricao=descricoes[i].strip(),
                        vistoria_id=vistoria.id
                    )
                    db.session.add(nova_foto)

        db.session.commit()  # commit final após adicionar todas as fotos

        # Histórico de edição
        if "user_id" in session:
            registrar_acao(
                usuario_id=session["user_id"],
                tipo_acao="edição",
                entidade="Vistoria",
                entidade_id=vistoria.id,
                observacao=f"Vistoria editada no endereço {vistoria.rua}, {vistoria.bairro}"
            )

        flash("✅ Vistoria atualizada com sucesso!", "success")
        return redirect(url_for("listar_vistorias"))

    return render_template("editar_vistoria.html", vistoria=vistoria)

@app.route("/vistoria/<int:id>/excluir", methods=["POST"])
def excluir_vistoria(id):
    # Verifica se o usuário está logado
    if "usuario" not in session:
        flash("⚠️ Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    # Verifica se é administrador
    usuario = User.query.get(session["user_id"])
    if usuario.cargo != "admin":
        flash("⚠️ Ação não permitida para seu perfil.", "warning")
        return redirect(url_for("listar_vistorias"))

    # Busca e tenta excluir a vistoria
    vistoria = VistoriaImovel.query.get_or_404(id)

    try:
        db.session.delete(vistoria)
        db.session.commit()

        # Registrar no histórico
        registrar_acao(
            usuario_id=usuario.id,
            tipo_acao="exclusão",
            entidade="Vistoria",
            entidade_id=id,
            observacao=f"Vistoria da rua {vistoria.rua}, nº {vistoria.numero} excluída."
        )

        flash("✅ Vistoria excluída com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Erro ao excluir: {str(e)}", "danger")

    return redirect(url_for("listar_vistorias"))



@app.route("/historico")
def historico():
    if session.get("cargo") != "admin":
        return redirect(url_for("dashboard"))

    tipo_acao = request.args.get("tipo")
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    query = HistoricoAcao.query

    if tipo_acao:
        query = query.filter_by(tipo_acao=tipo_acao)

    if data_inicio:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        query = query.filter(HistoricoAcao.data_hora >= inicio)

    if data_fim:
        fim = datetime.strptime(data_fim, "%Y-%m-%d")
        fim = fim.replace(hour=23, minute=59, second=59)
        query = query.filter(HistoricoAcao.data_hora <= fim)

    acoes = query.order_by(HistoricoAcao.data_hora.desc()).all()
    return render_template("historico.html", acoes=acoes)



def registrar_acao(usuario_id, tipo_acao, entidade, entidade_id, observacao=""):
    from models import HistoricoAcao, db
    acao = HistoricoAcao(
        usuario_id=usuario_id,
        tipo_acao=tipo_acao,
        entidade=entidade,
        entidade_id=entidade_id,
        observacao=observacao
    )
    db.session.add(acao)
    db.session.commit()

@app.route("/historico/exportar/pdf")
def exportar_historico_pdf():
    if session.get("cargo") != "admin":
        return redirect(url_for("dashboard"))

    acoes = HistoricoAcao.query.order_by(HistoricoAcao.data_hora.desc()).all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Histórico de Ações", ln=True, align="C")

    for a in acoes:
        linha = f"{a.data_hora.strftime('%d/%m/%Y %H:%M')} - {a.usuario.email} - {a.tipo_acao} - {a.entidade} #{a.entidade_id}"
        pdf.cell(200, 10, txt=linha, ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, download_name="historico_acoes.pdf", as_attachment=True)

@app.route("/historico/exportar/excel")
def exportar_historico_excel():
    if session.get("cargo") != "admin":
        return redirect(url_for("dashboard"))

    acoes = HistoricoAcao.query.order_by(HistoricoAcao.data_hora.desc()).all()
    dados = [{
        "ID": a.id,
        "Usuário": a.usuario.email,
        "Ação": a.tipo_acao,
        "Entidade": a.entidade,
        "ID Alvo": a.entidade_id,
        "Observação": a.observacao,
        "Data e Hora": a.data_hora.strftime('%d/%m/%Y %H:%M:%S')
    } for a in acoes]

    df = pd.DataFrame(dados)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="historico_acoes.xlsx", as_attachment=True)

# Listar obras
@app.route('/obras')
def obras():
    lista = Obra.query.all()
    return render_template('obras/obras_listar.html', obras=lista)


@app.route("/obras/nova", methods=["GET", "POST"])
def nova_obra():
    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        endereco = request.form["endereco"]
        responsavel = request.form["responsavel"]
        
        # CONVERTE as datas para datetime.date
        data_inicio = datetime.strptime(request.form["data_inicio"], "%Y-%m-%d").date()
        data_fim = datetime.strptime(request.form["data_fim"], "%Y-%m-%d").date()

        nova = Obra(
            nome=nome,
            descricao=descricao,
            endereco=endereco,
            responsavel=responsavel,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        db.session.add(nova)
        db.session.commit()
        usuario_id = session.get("user_id")
        registrar_acao(usuario_id, "criação", "obra", nova.id)
        flash("Obra criada com sucesso!", "success")
        return redirect(url_for("obras"))

    return render_template("obras/nova_obra.html")

@app.route('/obras/<int:id>/editar', methods=['GET', 'POST'])
def editar_obra(id):
    obra = Obra.query.get_or_404(id)

    if request.method == 'POST':
        nome_antigo = obra.nome
        obra.nome = request.form['nome']
        obra.descricao = request.form['descricao']
        obra.endereco = request.form['endereco']
        obra.responsavel = request.form['responsavel']

        data_inicio_str = request.form['data_inicio']
        data_fim_str = request.form['data_fim']
        obra.data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else None
        obra.data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else None

        db.session.commit()

        # Histórico de ação
        if 'user_id' in session:
            registrar_acao(
                usuario_id=session['user_id'],
                tipo_acao='editar',
                entidade='Obra',
                entidade_id=obra.id,
                observacao=f"Editou obra: '{nome_antigo}' para '{obra.nome}'"
            )


        flash('Obra atualizada com sucesso!', 'success')
        return redirect(url_for('obras'))

    return render_template('obras/editar_obra.html', obra=obra)

@app.route('/obras/<int:id>/deletar', methods=['POST'])
def deletar_obra(id):
    obra = Obra.query.get_or_404(id)
    db.session.delete(obra)
    db.session.commit()
    registrar_acao(session["user_id"], "exclusão", "obra", obra.id)

    return redirect(url_for('obras'))


@app.route("/obras/<int:id>/painel")
def painel_obra(id):
    obra = Obra.query.get_or_404(id)

    vistorias = VistoriaImovel.query.filter_by(obra_id=id).all()
    agendamentos = AgendamentoVistoria.query.filter_by(obra_id=id).all()
    #    agendamentos = AgendamentoVistoria.query.filter_by(obra_id=obra_id).all()

    comunicacoes = ComunicacaoObra.query.filter_by(obra_id=id).all()

    return render_template("obras/painel_obra.html",
                           obra=obra,
                           vistorias=vistorias,
                           agendamentos=agendamentos,
                           comunicacoes=comunicacoes)


def upload_bunny(nome_arquivo, caminho, api_key, pasta_destino=None):
    # Montar caminho final no BunnyCDN
    if pasta_destino:
        caminho_remoto = f"{pasta_destino}/{nome_arquivo}".replace(" ", "_")
    else:
        caminho_remoto = nome_arquivo.replace(" ", "_")

    # 🔒 URL de upload para a Storage Zone
    url = f"https://br.storage.bunnycdn.com/fotos-enotec-vistorias/{caminho_remoto}"

    headers = {
        "AccessKey": api_key,
        "Content-Type": "application/octet-stream"
    }

    with open(caminho, "rb") as f:
        r = requests.put(url, headers=headers, data=f)

    if r.status_code == 201:
        # 🌐 URL pública via Pull Zone
        return f"https://enotec-vistorias.b-cdn.net/{caminho_remoto}"
    else:
        print("❌ Erro no upload Bunny:", r.status_code, r.text)
        return None



# Rota para upload de múltiplas fotos com título associadas a uma vistoria
@app.route("/vistoria/<int:id>/upload_fotos", methods=["POST"])
def upload_fotos(id):
    vistoria = VistoriaImovel.query.get_or_404(id)
    fotos = request.files.getlist("fotos")
    titulos = request.form.getlist("titulos")  # campo extra do formulário

    api_key = "7fc78fa7-ff70-4921-bcc75dd59e58-588a-4188"

    for i, foto in enumerate(fotos):
        if not foto:
            continue
        
        nome_arquivo = secure_filename(f"vistoria_{id}_{foto.filename.replace(' ', '_')}")
        os.makedirs("temp", exist_ok=True)
        caminho_temporario = os.path.join("temp", nome_arquivo)
        foto.save(caminho_temporario)

        url_bunny = upload_imagem_bunny(nome_arquivo, caminho_temporario, api_key)
        os.remove(caminho_temporario)

        if url_bunny:
            nova_foto = FotoVistoria(
                url=url_bunny,
                descricao=titulos[i] if i < len(titulos) else "",
                vistoria_id=id
            )
            db.session.add(nova_foto)

    db.session.commit()
    flash("✅ Fotos enviadas com sucesso!", "success")
    return redirect(url_for("editar_vistoria", id=id))

@app.route("/admin/fotos")
def admin_fotos():
    obras = Obra.query.all()
    return render_template("obras/fotos_por_obra.html", obras=obras)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Banco criado/atualizado!")
    app.run(host="0.0.0.0", port=5000,debug=True)
