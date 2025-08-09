import os
import requests
from werkzeug.utils import secure_filename
from urllib.parse import quote

# Configurações do BunnyCDN
BUNNY_STORAGE_ZONE = "fotos-enotec-vistorias"
BUNNY_BUCKET_URL = f"br.storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}"
BUNNY_PUBLIC_URL = f"https://{BUNNY_BUCKET_URL}"
BUNNY_ACCESS_KEY = "7fc78fa7-ff70-4921-bcc75dd59e58-588a-4188"

def upload_foto_vistoria(token, obra_nome, vistoria_id, foto_file):
    """
    Envia uma foto para o BunnyCDN na estrutura:
    Relatorios/fotos/vistorias/{{obra_nome}}/Vistoria_{{id}}/
    """
    obra_nome_slug = slugify(obra_nome)
    pasta = f"Relatorios/fotos/vistorias/{obra_nome_slug}/Vistoria_{vistoria_id}"
    filename = secure_filename(foto_file.filename)
    caminho_completo = f"{pasta}/{filename}"

    url_destino = f"https://{BUNNY_BUCKET_URL}/{quote(caminho_completo)}"
    headers = {
        "AccessKey": token,
        "Content-Type": "application/octet-stream"
    }

    response = requests.put(url_destino, headers=headers, data=foto_file.stream)

    if response.status_code in [200, 201]:
        url_publica = f"{BUNNY_PUBLIC_URL}/{quote(caminho_completo)}"
        return {
            "url": url_publica,
            "nome": filename
        }
    else:
        raise Exception(f"Erro ao enviar para BunnyCDN: {response.status_code} - {response.text}")


def slugify(value):
    import re
    import unicodedata
    value = str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)
