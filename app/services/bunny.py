import requests

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
