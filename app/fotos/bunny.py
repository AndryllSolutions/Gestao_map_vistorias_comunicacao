# app/fotos/bunny.py
import os
import re
import unicodedata
import requests
from werkzeug.datastructures import FileStorage

# .env
BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE", "fotos-enotec-vistorias")
BUNNY_STORAGE_URL  = os.getenv("BUNNY_STORAGE_URL", f"https://br.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}")
BUNNY_ACCESS_KEY   = os.getenv("BUNNY_STORAGE_KEY")
BUNNY_PULL_ZONE    = os.getenv("BUNNY_PULL_ZONE", f"{BUNNY_STORAGE_ZONE}.b-cdn.net")  # opcional, mas útil

def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s.-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text

def upload_foto_vistoria(obra_nome: str, vistoria_id: int, foto_file: FileStorage) -> dict:
    """
    Sobe uma foto para o BunnyCDN em:
      /Relatorios/fotos/vistorias/{obra_slug}/{vistoria_id}/{arquivo}
    Retorna: {"url": "<url_publica>", "nome": "<arquivo>"}
    """
    if not BUNNY_ACCESS_KEY or not BUNNY_STORAGE_URL:
        raise RuntimeError("Config Bunny ausente: defina BUNNY_STORAGE_KEY e BUNNY_STORAGE_URL no .env")

    obra_slug = _slugify(obra_nome or "obra")
    nome_arquivo = _slugify(foto_file.filename or "foto.jpg")
    caminho_relativo = f"Relatorios/fotos/vistorias/{obra_slug}/{vistoria_id}/{nome_arquivo}"

    url_upload = f"{BUNNY_STORAGE_URL}/{caminho_relativo}"

    headers = {
        "AccessKey": BUNNY_ACCESS_KEY,
        "Content-Type": "application/octet-stream",
    }

    # importante: voltar o ponteiro caso o FileStorage já tenha sido lido antes
    if hasattr(foto_file, "stream"):
        try:
            foto_file.stream.seek(0)
        except Exception:
            pass

    resp = requests.put(url_upload, headers=headers, data=foto_file.read())
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Erro Bunny {resp.status_code}: {resp.text}") from e

    url_publica = f"https://{BUNNY_PULL_ZONE}/{caminho_relativo}"
    return {"url": url_publica, "nome": nome_arquivo}
