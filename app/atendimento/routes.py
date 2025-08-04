# app/atendimento/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, time
from werkzeug.utils import secure_filename
import os
from ..models import Obra  # se ainda não tiver importado
from ..models import db, ComunicacaoObra, VistoriaImovel, FotoVistoria
from ..utils import registrar_acao
from ..services.bunny import upload_bunny  # se existir
from flask import Blueprint
from flask_login import current_user

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

    comunicacoes = ComunicacaoObra.query.filter(~ComunicacaoObra.vistorias.any()).all()


    registros = []

    for c in comunicacoes:
        registros.append({
            "id": c.id,
            "nome": c.nome,
            "rua": c.endereco,
            "obra": c.obra,
            "data_envio": c.data_envio,
            "finalizada": False,
            "comunicador": f"{c.usuario.nome} (Admin)" if c.usuario and c.usuario.cargo == "admin" else c.usuario.nome if c.usuario else "—"
        })

    vistorias = VistoriaImovel.query.all()

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

    # Deleta fotos se houver
    for foto in vistoria.fotos:
        db.session.delete(foto)

    db.session.delete(vistoria)
    if comunicacao:
        db.session.delete(comunicacao)

    db.session.commit()

    flash(f"❌ Atendimento #{id} excluído com sucesso!", "success")
    return redirect(url_for("atendimento.dashboard_unificado"))

@atendimento_bp.route("/nova")
def nova_comunicacao_vistoria():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    obras = Obra.query.all()
    return render_template("atendimento/formulario.html", obras=obras, comunicacao=None, vistoria=None)


@atendimento_bp.route("/criar", methods=["POST"])
def criar_atendimento():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    nome = request.form.get("nome")
    endereco = request.form.get("endereco")
    obra_id = request.form.get("obra_id")
    
    # VALIDAÇÃO
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
        usuario_id=session["user_id"]  # ✅ salva o vistoriador
    )
    db.session.add(nova_vistoria)
    db.session.commit()

    return redirect(url_for("atendimento.atendimento_unificado", id=nova_vistoria.id))



@atendimento_bp.route("/<int:id>", methods=["GET", "POST"])
def atendimento_unificado(id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    vistoria = VistoriaImovel.query.get_or_404(id)
    comunicacao = vistoria.comunicacao
    obras = Obra.query.all()
    if request.method == "POST":
        # Atualiza dados da comunicação
        if comunicacao:
            comunicacao.nome = request.form.get("nome")
            comunicacao.cpf = request.form.get("cpf")
            comunicacao.telefone = request.form.get("telefone")
            comunicacao.endereco = request.form.get("endereco")
            comunicacao.comunicado = request.form.get("comunicado")
            comunicacao.economia = request.form.get("economia")
            comunicacao.tipo_imovel = request.form.get("tipo_imovel")
            comunicacao.obra_id = request.form.get("obra_id") or None


        # Atualiza dados da vistoria
        vistoria.finalizada = True if request.form.get("finalizada") else False
        vistoria.obra_id = request.form.get("obra_id") or None

        # Datas e horas das tentativas
        for i in range(1, 4):
            data = request.form.get(f"data_{i}")
            hora = request.form.get(f"hora_{i}")
            if data:
                setattr(vistoria, f"data_{i}", datetime.strptime(data, "%Y-%m-%d").date())
            if hora:
                setattr(vistoria, f"hora_{i}", datetime.strptime(hora, "%H:%M").time())

        db.session.commit()
        flash("✅ Atendimento atualizado com sucesso!")
        return redirect(url_for("atendimento.dashboard_unificado"))

        # Se for GET, renderiza a tela
    return render_template("atendimento/formulario.html",
                           vistoria=vistoria,
                           comunicacao=comunicacao,
                           obras=obras)
