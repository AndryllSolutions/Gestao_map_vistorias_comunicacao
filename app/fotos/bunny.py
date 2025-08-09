import os
import requests
from werkzeug.utils import secure_filename

BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE", "fotos-enotec-vistorias")
BUNNY_ACCESS_KEY = os.getenv("BUNNY_STORAGE_KEY")
BUNNY_STORAGE_URL = os.getenv("BUNNY_STORAGE_URL", f"https://br.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}")

def upload_foto_vistoria(obra_nome, vistoria_id, foto_file):
    """
    Faz upload de uma imagem para a BunnyCDN na pasta /Relatorios/fotos/vistorias/{obra_nome}/{vistoria_id}/
    Substitui espaços por "_" no nome da obra.
    """
    # Segurança: substituir espaços por _
    obra_nome_sanitizado = obra_nome.replace(" ", "_")

    if not BUNNY_ACCESS_KEY or not BUNNY_STORAGE_URL:
        raise RuntimeError("❌ Configuração BunnyCDN ausente (BUNNY_ACCESS_KEY ou BUNNY_STORAGE_URL).")

    nome_seguro = secure_filename(foto_file.filename)
    obra_nome_sanitizado = obra_nome.replace(" ", "_")
    caminho_bunny = f"Relatorios/fotos/vistorias/{obra_nome_sanitizado}/{vistoria_id}/{nome_seguro}"

    url_destino = f"{BUNNY_STORAGE_URL}/{caminho_bunny}"

    headers = {
        "AccessKey": BUNNY_ACCESS_KEY,
        "Content-Type": "application/octet-stream"
    }

    try:
        response = requests.put(url_destino, data=foto_file.read(), headers=headers)
        response.raise_for_status()

        url_final = f"https://{BUNNY_STORAGE_ZONE}.b-cdn.net/{caminho_bunny}"
        return {
            "url": url_final,
            "nome": nome_seguro
        }

    except Exception as e:
        raise RuntimeError(f"Erro ao enviar imagem para BunnyCDN: {str(e)}")
