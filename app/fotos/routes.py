import os
import requests
from flask import Blueprint, request, render_template, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from app.extensions import db
from app.models import FotoVistoria
from app.fotos.bunny import upload_foto_vistoria
import requests

load_dotenv()

fotos_bp = Blueprint("fotos", __name__, template_folder="templates")

@fotos_bp.route("/fotos/upload/<int:obra_id>/<int:vistoria_id>", methods=["GET", "POST"])
def upload_fotos_bunny(obra_id, vistoria_id):
    if request.method == "POST":
        fotos = request.files.getlist("fotos")
        if not fotos or fotos[0].filename == "":
            flash("⚠️ Nenhuma foto selecionada para envio.", "warning")
            return redirect(request.url)

        sucesso = 0
        erros = []
        fotos_enviadas = []

        for foto in fotos:
            try:
                # 🔄 Chama a função central de upload com nome da obra em branco (ou você pode buscar o nome da obra se quiser)
                url_final = upload_foto_vistoria(obra_nome=f"{obra_id}", vistoria_id=vistoria_id, foto=foto)
                if url_final:
                    nova_foto = FotoVistoria(
                        vistoria_id=vistoria_id,
                        url=url_final,
                        titulo=foto.filename,
                        descricao="",
                    )
                    db.session.add(nova_foto)
                    sucesso += 1
                    fotos_enviadas.append(foto.filename)
                else:
                    erros.append((foto.filename, "Erro no upload"))
            except Exception as e:
                erros.append((foto.filename, "Exception", str(e)))

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar no banco: {e}", "danger")

        if sucesso:
            flash(f"✅ {sucesso} foto(s) enviadas com sucesso.", "success")
        if erros:
            flash(f"❌ {len(erros)} erro(s) ao enviar: {', '.join([e[0] for e in erros])}", "danger")

        return render_template("fotos/upload_fotos.html", obra_id=obra_id, vistoria_id=vistoria_id, fotos_enviadas=fotos_enviadas)

    return render_template("fotos/upload_fotos.html", obra_id=obra_id, vistoria_id=vistoria_id)


@fotos_bp.route("/fotos/excluir/<int:foto_id>", methods=["POST"])
def excluir_foto(foto_id):
    foto = FotoVistoria.query.get_or_404(foto_id)
    try:
        db.session.delete(foto)
        db.session.commit()
        flash("🗑️ Foto excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir foto: {e}", "danger")
    return redirect(request.referrer or url_for("atendimento.dashboard_unificado"))
