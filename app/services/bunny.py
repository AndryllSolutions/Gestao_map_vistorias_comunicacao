# app/services/bunny.py
import os
import mimetypes
import requests
from flask import current_app
from urllib.parse import quote

def _slugify(texto: str) -> str:
    s = (texto or "SemObra").lower()
    for a, b in [
        (' ', '-'), ('ç','c'),
        ('á','a'), ('à','a'), ('â','a'), ('ã','a'),
        ('é','e'), ('ê','e'),
        ('í','i'),
        ('ó','o'), ('ô','o'), ('õ','o'),
        ('ú','u'), ('ü','u')
    ]:
        s = s.replace(a, b)
    return s

def _get_cfg():
    """Lê config primeiro do app.config e cai para os.environ. Só é chamado dentro de contexto."""
    storage_url = (current_app.config.get("BUNNY_STORAGE_URL")
                   or os.environ.get("BUNNY_STORAGE_URL"))
    storage_key = (current_app.config.get("BUNNY_STORAGE_KEY")
                   or os.environ.get("BUNNY_STORAGE_KEY"))
    public_base = (current_app.config.get("BUNNY_PUBLIC_BASE")
                   or os.environ.get("BUNNY_PUBLIC_BASE"))
    if not storage_url or not storage_key or not public_base:
        raise RuntimeError(
            "Config Bunny ausente: defina BUNNY_STORAGE_URL, BUNNY_STORAGE_KEY e BUNNY_PUBLIC_BASE no .env"
        )
    return storage_url, storage_key, public_base

def upload_bunny(obra_nome, vistoria_id, file_storage):
    """
    Envia uma foto para a Bunny Storage e retorna {"url": <url_publica>, "path": <caminho>}.
    Compatível com: from ..services.bunny import upload_bunny
    """
    storage_url, storage_key, public_base = _get_cfg()

    obra_slug = _slugify(obra_nome)
    # filename seguro em URL (mantém . _ - ( ) )
    raw_name = file_storage.filename or "arquivo"
    filename = quote(raw_name, safe="._-()")  # faz URL-encode de espaços e acentos
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or "application/octet-stream"

    path_in_storage = f"Relatorios/fotos/vistorias/{obra_slug}/{vistoria_id}/{filename}"
    destino = f"{storage_url}/{path_in_storage}"

    r = requests.put(
        destino,
        data=file_storage.stream.read(),
        headers={"AccessKey": storage_key, "Content-Type": mime},
        timeout=60,
    )
    r.raise_for_status()

    url_publica = f"{public_base}/{path_in_storage}"
    return {"url": url_publica, "path": path_in_storage}
