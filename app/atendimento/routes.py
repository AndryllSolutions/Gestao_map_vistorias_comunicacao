# app/atendimento/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, time
from werkzeug.utils import secure_filename
import os
from ..models import Obra, db, ComunicacaoObra, VistoriaImovel, FotoVistoria
from ..utils import registrar_acao
from ..services.bunny import upload_bunny
from flask_login import current_user
from sqlalchemy.orm import joinedload
from dateutil import parser  # se ainda não tiver
from flask import send_file  # se ainda não estiver
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black
from textwrap import wrap
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from io import BytesIO
from dateutil import parser

def parse_hora(hora_str):
    try:
        return datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        return datetime.strptime(hora_str, "%H:%M:%S").time()

atendimento_bp = Blueprint('atendimento', __name__, template_folder='../../templates/atendimento')

@atendimento_bp.route("/")
def dashboard_unificado():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    cargo = session.get("cargo")
    user_id = session.get("user_id")
    registros = []

    # 👇 OBRAS VISÍVEIS PARA O USUÁRIO (vistoriador = só a obra vinculada)
    if cargo == "vistoriador":
        from app.models import User  # necessário se current_user não está funcionando
        usuario = User.query.get(user_id)
        obras_ids = [usuario.obra_id] if usuario and usuario.obra_id else []
    else:
        obras_ids = [obra.id for obra in Obra.query.all()]

    # 🗂️ Buscar os registros conforme a obra_id permitida
    comunicacoes = ComunicacaoObra.query.filter(ComunicacaoObra.obra_id.in_(obras_ids)).all()
    vistorias = VistoriaImovel.query.filter(VistoriaImovel.obra_id.in_(obras_ids)).options(joinedload(VistoriaImovel.usuario)).all()

    # 🧽 Evita duplicação: só mostra comunicações sem vistoria associada
    ids_com_com_vistoria = [v.comunicacao_id for v in vistorias if v.comunicacao_id]

    for c in comunicacoes:
        if c.id not in ids_com_com_vistoria:
            registros.append({
                "id": c.id,
                "nome": c.nome,
                "rua": c.endereco,
                "obra": c.obra,
                "data_envio": c.data_envio,
                "finalizada": False,
                "comunicador": f"{c.usuario.nome} (Admin)" if c.usuario and c.usuario.cargo == "admin" else c.usuario.nome if c.usuario else "—"
            })

    for v in vistorias:
        registros.append({
            "id": v.id,
            "nome": v.nome_responsavel or (v.comunicacao.nome if v.comunicacao else "Sem nome"),
            "rua": v.rua or (v.comunicacao.endereco if v.comunicacao else "—"),
            "obra": v.obra,
            "data_envio": v.data_1,
            "finalizada": v.finalizada,
            "comunicador": (
                f"{v.comunicacao.usuario.nome} (Admin)" if v.comunicacao and v.comunicacao.usuario and v.comunicacao.usuario.cargo == "admin"
                else v.comunicacao.usuario.nome if v.comunicacao and v.comunicacao.usuario
                else "—"
            ),
            "vistoriador": (
                f"{v.usuario.nome} (Admin)" if v.usuario and v.usuario.cargo == "admin"
                else v.usuario.nome if v.usuario else "—"
            ),
        })

    registros.sort(
        key=lambda r: datetime.combine(r["data_envio"], time.min) if r.get("data_envio") else datetime.min,
        reverse=True
    )

    return render_template("atendimento/dashboard.html",
                           registros=registros,
                           total_comunicacoes=len(comunicacoes),
                           total_vistorias=len(vistorias),
                           total_registros=len(registros))




@atendimento_bp.app_template_filter('getattr_safe')
def getattr_safe(obj, attr):
    return getattr(obj, attr, '')

@atendimento_bp.route("/<int:id>/delete", methods=["POST"])
def deletar_atendimento(id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("cargo") != "admin":
        flash("Apenas administradores podem excluir atendimentos.", "danger")
        return redirect(url_for("atendimento.dashboard_unificado"))

    vistoria = VistoriaImovel.query.get_or_404(id)
    comunicacao = vistoria.comunicacao

    for foto in vistoria.fotos:
        db.session.delete(foto)

    db.session.delete(vistoria)
    if comunicacao:
        db.session.delete(comunicacao)

    db.session.commit()

    registrar_acao(
        tipo_acao="exclusão",
        entidade="VistoriaImovel",
        entidade_id=vistoria.id,
        usuario_id=session["user_id"],
        observacao=f"Atendimento vinculado à comunicação #{comunicacao.id if comunicacao else '—'} foi excluído."
    )

    if comunicacao:
        registrar_acao(
            tipo_acao="exclusão",
            entidade="ComunicacaoObra",
            entidade_id=comunicacao.id,
            usuario_id=session["user_id"],
            observacao=f"Comunicação associada à vistoria #{vistoria.id} foi excluída."
        )

    flash(f"❌ Atendimento #{id} excluído com sucesso!", "success")
    return redirect(url_for("atendimento.dashboard_unificado"))

@atendimento_bp.route("/nova")
def nova_comunicacao_vistoria():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    obras = Obra.query.all()
    return render_template(
    "atendimento/formulario.html",
    obras=obras,
    comunicacao=None,
    vistoria=None
)


@atendimento_bp.route("/criar", methods=["POST"])
def criar_atendimento():
    if "user_id" not in session:
        flash("⚠️ Sessão inválida. Faça login novamente.", "danger")
        return redirect(url_for("auth.login"))

    nome = request.form.get("nome")
    endereco = request.form.get("endereco")
    obra_id = request.form.get("obra_id")

    if not nome or not endereco or not obra_id:
        flash("⚠️ Nome, endereço e obra são obrigatórios!", "danger")
        return redirect(url_for("atendimento.nova_comunicacao_vistoria"))

    nova_comunicacao = ComunicacaoObra(
        nome=nome,
        cpf=request.form.get("cpf"),
        telefone=request.form.get("telefone"),
        endereco=endereco,
        numero=request.form.get("numero"),
        bairro=request.form.get("bairro"),
        comunicado=request.form.get("comunicado"),
        economia=request.form.get("economia"),
        tipo_imovel=request.form.get("tipo_imovel"),
        data_envio=datetime.now(),
        usuario_id=session["user_id"],
        obra_id=obra_id
    )

    db.session.add(nova_comunicacao)
    db.session.flush()

    nova_vistoria = VistoriaImovel(
    comunicacao_id=nova_comunicacao.id,
    data_1=datetime.now().date(),
    hora_1=datetime.now().time(),   
    obra_id=obra_id,
    usuario_id=session["user_id"] if session.get("cargo") == "vistoriador" else None
)


    db.session.add(nova_vistoria)
    db.session.commit()

    registrar_acao(
        tipo_acao="criação",
        entidade="ComunicacaoObra",
        entidade_id=nova_comunicacao.id,
        usuario_id=session["user_id"],
        observacao=f"Comunicação criada para '{nova_comunicacao.nome}' na obra ID {obra_id}."
    )

    registrar_acao(
        tipo_acao="criação",
        entidade="VistoriaImovel",
        entidade_id=nova_vistoria.id,
        usuario_id=session["user_id"],
        observacao=f"Vistoria inicial registrada para comunicação ID {nova_comunicacao.id}."
    )

    flash("✅ Atendimento criado com sucesso!", "success")
    return redirect(url_for("atendimento.atendimento_unificado", id=nova_vistoria.id))

@atendimento_bp.route("/<int:id>", methods=["GET", "POST"])
def atendimento_unificado(id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    vistoria = VistoriaImovel.query.get_or_404(id)
    comunicacao = vistoria.comunicacao
    obras = Obra.query.all()

    if request.method == "POST":
        cargo = session.get("cargo")
        if comunicacao and cargo in ["admin", "comunicador"]:
            comunicacao.nome = request.form.get("nome")
            comunicacao.cpf = request.form.get("cpf")
            comunicacao.telefone = request.form.get("telefone")
            comunicacao.endereco = request.form.get("endereco")
            comunicacao.numero = request.form.get("numero")
            comunicacao.bairro = request.form.get("bairro")
            comunicacao.comunicado = request.form.get("comunicado")
            comunicacao.economia = request.form.get("economia")
            comunicacao.tipo_imovel = request.form.get("tipo_imovel")
            comunicacao.obra_id = request.form.get("obra_id") or None

        vistoria.finalizada = True if request.form.get("finalizada") else False
        vistoria.obra_id = request.form.get("obra_id") or None
        vistoria.tipo_imovel = request.form.get("tipo_imovel")
        vistoria.soleira = request.form.get("soleira")
        vistoria.calcada = request.form.get("calcada")
        vistoria.observacoes = request.form.get("observacoes")
        vistoria.nome_responsavel = request.form.get("nome")
        vistoria.cpf_responsavel = request.form.get("cpf")
        vistoria.tipo_vinculo = request.form.get("vinculo")
        vistoria.rua = request.form.get("endereco")
        vistoria.numero = request.form.get("numero")
        vistoria.bairro = request.form.get("bairro")

        for i in range(1, 4):
            data = request.form.get(f"data_{i}")
            hora = request.form.get(f"hora_{i}")
            if data:
                try:
                    setattr(vistoria, f"data_{i}", datetime.strptime(data, "%Y-%m-%d").date())
                except ValueError:
                    flash(f"⚠️ Data inválida no campo data_{i}.", "danger")
            if hora:
                try:
                    hora_convertida = parser.parse(hora).time()
                    setattr(vistoria, f"hora_{i}", hora_convertida)
                except (ValueError, TypeError):
                    flash(f"⚠️ Hora inválida no campo hora_{i}.", "danger")

        vistoriador_assumiu = False
        if not vistoria.usuario_id and session.get("cargo") == "vistoriador":
            vistoria.usuario_id = session["user_id"]
            vistoriador_assumiu = True

        db.session.commit()

        registrar_acao(
            tipo_acao="edição",
            entidade="VistoriaImovel",
            entidade_id=vistoria.id,
            usuario_id=session["user_id"],
            observacao=f"Vistoria editada no atendimento #{vistoria.id}."
        )

        if comunicacao:
            registrar_acao(
                tipo_acao="edição",
                entidade="ComunicacaoObra",
                entidade_id=comunicacao.id,
                usuario_id=session["user_id"],
                observacao=f"Comunicação editada no atendimento #{comunicacao.id}."
            )

        flash("✅ Atendimento atualizado com sucesso!", "success")
        if vistoriador_assumiu:
            flash("📌 Agora você é o responsável por esta vistoria.", "info")

        return redirect(url_for("atendimento.dashboard_unificado"))

    return render_template("atendimento/formulario.html",
                           vistoria=vistoria,
                           comunicacao=comunicacao,
                           obras=obras)


@atendimento_bp.route("/<int:id>/assumir", methods=["POST"])
def assumir_vistoria(id):
    if "user_id" not in session or session.get("cargo") != "vistoriador":
        flash("Permissão negada.", "danger")
        return redirect(url_for("auth.login"))

    vistoria = VistoriaImovel.query.get_or_404(id)

    if not vistoria.usuario_id:
        vistoria.usuario_id = session["user_id"]
        db.session.commit()
        flash("📌 Você assumiu a vistoria com sucesso!", "info")
    else:
        flash("⚠️ Esta vistoria já foi assumida por outro usuário.", "warning")

    return redirect(url_for("atendimento.atendimento_unificado", id=id))


@atendimento_bp.route("/relatorio/pdf/<int:id>")
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


@atendimento_bp.route("/relatorio/excel/<int:id>")
def gerar_excel_vistoria(id):
    if "user_id" not in session or session.get("cargo") not in ["admin", "vistoriador"]:
        flash("Acesso restrito a administradores e vistoriadores.", "danger")
        return redirect(url_for("auth.login"))

    vistoria = VistoriaImovel.query.get_or_404(id)

    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    buffer = BytesIO()

    wb = Workbook()
    ws = wb.active
    ws.title = "Laudo Vistoria"

    dados = [
        ["Campo", "Valor"],
        ["Data da Vistoria", f"{vistoria.data_1 or ''} {vistoria.hora_1 or ''}"],
        ["Responsável", vistoria.nome_responsavel or ''],
        ["CPF", vistoria.cpf_responsavel or ''],
        ["Vínculo", vistoria.tipo_vinculo or ''],
        ["Endereço", f"{vistoria.rua}, {vistoria.numero} - {vistoria.bairro}, {vistoria.municipio}"],
        ["Tipo de Imóvel", vistoria.tipo_imovel or ''],
        ["Soleira", vistoria.soleira or ''],
        ["Calçada", vistoria.calcada or ''],
        ["Obra", vistoria.obra.nome if vistoria.obra else ''],
        ["Observações", vistoria.observacoes or '']
    ]

    for row in dados:
        ws.append(row)
    for col in range(1, 3):
        ws.column_dimensions[get_column_letter(col)].width = 35

    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"laudo_vistoria_{id}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@atendimento_bp.route("/relatorio/comunicacoes/excel")
def exportar_comunicacoes_excel():
    if "user_id" not in session or session.get("cargo") not in ["admin", "vistoriador"]:
        flash("Acesso restrito a administradores e vistoriadores.", "danger")
        return redirect(url_for("auth.dashboard"))

    buffer = BytesIO()
    wb = Workbook()

    # 1. Aba Geral com todas as comunicações
    ws_geral = wb.active
    ws_geral.title = "Relatório Geral"
    ws_geral.append(["ID", "Nome", "Telefone", "Endereço", "Número", "Bairro", "Obra", "Data Envio"])

    comunicacoes = ComunicacaoObra.query.all()
    for c in comunicacoes:
        ws_geral.append([
            c.id,
            c.nome,
            c.telefone,
            c.endereco,
            c.numero,
            c.bairro,
            c.obra.nome if c.obra else "—",
            c.data_envio.strftime("%d/%m/%Y %H:%M") if c.data_envio else ""
        ])

    # 2. Criar aba para cada obra
    obras = Obra.query.all()
    for obra in obras:
        nome_aba = obra.nome[:31]  # Excel aceita no máx 31 caracteres no título
        ws_obra = wb.create_sheet(title=nome_aba)
        ws_obra.append(["ID", "Nome", "Telefone", "Endereço", "Número", "Bairro", "Data Envio"])

        comunicacoes_obra = ComunicacaoObra.query.filter_by(obra_id=obra.id).all()
        for c in comunicacoes_obra:
            ws_obra.append([
                c.id,
                c.nome,
                c.telefone,
                c.endereco,
                c.numero,
                c.bairro,
                c.data_envio.strftime("%d/%m/%Y %H:%M") if c.data_envio else ""
            ])

    # Finaliza e retorna
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="relatorio_comunicacoes.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
