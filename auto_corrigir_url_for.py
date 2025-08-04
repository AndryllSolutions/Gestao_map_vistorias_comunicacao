import os
import re
import subprocess

TEMPLATES_DIR = "templates"
BACKUP_SUFFIX = ".bak"

def get_blueprint_routes():
    print("🔎 Lendo endpoints com flask routes...\n")
    output = subprocess.check_output(["flask", "routes"], text=True)
    endpoints = {}
    for line in output.splitlines()[2:]:  # pula header
        parts = line.split()
        if len(parts) >= 3:
            endpoint = parts[0]
            route = parts[-1]
            endpoints[endpoint.split('.')[-1]] = endpoint  # editar_obra -> obras.editar_obra
    return endpoints

def corrigir_url_for(template_path, endpoint_map):
    with open(template_path, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Backup
    with open(template_path + BACKUP_SUFFIX, "w", encoding="utf-8") as f:
        f.write(conteudo)

    padrao = re.compile(r"url_for\(\s*['\"]([\w_]+)['\"]\s*(?:,|\))")
    alterado = False

    def substituir(match):
        nome = match.group(1)
        if nome in endpoint_map:
            novo = endpoint_map[nome]
            if novo != nome:
                print(f"  🛠 Corrigindo: {nome} -> {novo}")
                nonlocal alterado
                alterado = True
                return f"url_for('{novo}'"
        return match.group(0)

    novo_conteudo = padrao.sub(substituir, conteudo)

    if alterado:
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        return True
    return False

def main():
    endpoint_map = get_blueprint_routes()
    print(f"🔍 Endpoints detectados: {len(endpoint_map)}\n")

    total_corrigidos = 0
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for nome_arquivo in files:
            if nome_arquivo.endswith(".html"):
                caminho = os.path.join(root, nome_arquivo)
                print(f"📄 Verificando: {caminho}")
                if corrigir_url_for(caminho, endpoint_map):
                    total_corrigidos += 1
                    print(f"✅ Corrigido: {nome_arquivo}\n")
                else:
                    print(f"🟢 Nenhuma alteração necessária.\n")

    print("🚀 Finalizado!")
    print(f"Total de arquivos modificados: {total_corrigidos}")

if __name__ == "__main__":
    main()
