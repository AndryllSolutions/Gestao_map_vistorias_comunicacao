from flask import Flask, request, jsonify, render_template, redirect, session,url_for,send_file,flash
from flask_cors import CORS
from models import db, User, Imovel,ComunicacaoObra,VistoriaImovel,AgendamentoVistoria,HistoricoAcao,Obra
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask_migrate import Migrate
from textwrap import wrap
from sqlalchemy import and_
import pandas as pd
from fpdf import FPDF
from flask_migrate import Migrate
from datetime import timedelta,datetime


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

    novo_usuario = User(email=email, password=senha)
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

    # Normaliza o e-mail e a senha (remove espaços e coloca em minúsculo)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    user = User.query.filter_by(email=email, password=password).first()
    if user:
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

@app.route("/comunicacoes", methods=["GET"])
def listar_comunicacoes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    registros = ComunicacaoObra.query.order_by(ComunicacaoObra.id.desc()).all()
    return render_template("comunicacoes_dashboard.html", registros=registros)

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
        obra_id=obra_id if obra_id else None  # 👈 ESSA LINHA
    )

        db.session.add(nova)
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

        return redirect(url_for("vistoria"))
    
    obras = Obra.query.all()
    flash("✅ Vistoria registrada com sucesso!")
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

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "LAUDO DA VISTORIA CAUTELAR")
    y -= 40

    # Dados da vistoria
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
    y -= 30

    # Norma Técnica
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

    # LGPD
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
    # Ciência do Morador
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Ciência do Morador quanto à Vistoria")
    y -= 20
    ciencia_texto = (
        f"Eu, {vistoria.nome_responsavel or '________________'}, portador do CPF {vistoria.cpf_responsavel or '________________'}, "
        "declaro que forneci de livre e espontânea vontade todas as informações referentes ao meu imóvel e estou ciente "
        "das fotografias e observações registradas durante a vistoria. Confirmo que estou de acordo com o conteúdo deste laudo."
    )
    y = draw_wrapped_text(ciencia_texto, 50, y)

    # Assinatura
    y -= 40
    c.drawString(50, y, "________________________________________")
    y -= 15
    c.drawString(50, y, "Assinatura do Responsável")

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
        vistoria.municipio = request.form["municipio"]
        vistoria.bairro = request.form["bairro"]
        vistoria.rua = request.form["rua"]
        vistoria.data_1 = datetime.strptime(request.form["data_1"], "%Y-%m-%d").date()
        vistoria.hora_1 = datetime.strptime(request.form["hora_1"], "%H:%M").time()  # ← aqui a correção
        vistoria.tipo_imovel = request.form["tipo_imovel"]
        vistoria.observacoes = request.form["observacoes"]

        db.session.commit()

        # Registrar histórico
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Banco criado/atualizado!")
    app.run(host="0.0.0.0", port=5000,debug=True)
