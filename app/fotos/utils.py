import os
import requests

BUNNY_STORAGE_URL = os.getenv("BUNNY_STORAGE_URL")
BUNNY_STORAGE_KEY = os.getenv("BUNNY_STORAGE_KEY")

def upload_foto_bunny(foto_file, obra_id, vistoria_id, filename):
    if not BUNNY_STORAGE_URL or not BUNNY_STORAGE_KEY:
        print("❌ BunnyCDN não configurado corretamente.")
        return None

    caminho = f"Obra_{obra_id}/Vistoria_{vistoria_id}/{filename}"
    url = f"{BUNNY_STORAGE_URL}/{caminho}"

    headers = {
        "AccessKey": BUNNY_STORAGE_KEY,
        "Content-Type": "application/octet-stream"
    }

    response = requests.put(url, headers=headers, data=foto_file.read())
    if response.status_code == 201:
        return url
    else:
        print(f"❌ Falha ao subir {filename}: {response.status_code} - {response.text}")
        return None
