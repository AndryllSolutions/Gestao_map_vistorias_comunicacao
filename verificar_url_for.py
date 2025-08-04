import os
import re
import subprocess

def coletar_endpoints():
    print("🔎 Coletando endpoints com flask routes...")
    result = subprocess.run(["flask", "routes"], capture_output=True, text=True)
    endpoints = {}
    for line in result.stdout.splitlines():
        if '.' in line and '/' in line:
            parts = line.split()
            endpoint = parts[0]
            endpoints[endpoint.split('.')[-1]] = endpoint
    return endpoints

def buscar_url_for_em_templates():
    print("📁 Varredura dos templates...")
    templates_dir = os.path.join(os.getcwd(), 'templates')
    usados = []
    for root, dirs, files in os.walk(templates_dir):
        for filename in files:
            if filename.endswith('.html'):
                path = os.path.join(root, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f.readlines(), 1):
                        matches = re.findall(r"url_for\(\s*[\"']([\w_]+)[\"']", line)
                        for match in matches:
                            usados.append((match, path, i, line.strip()))
    return usados

def main():
    usados = buscar_url_for_em_templates()
    endpoints = coletar_endpoints()

    print("\n🚨 Sugestões de correção:\n")
    for nome_usado, arquivo, linha, conteudo in usados:
        if nome_usado not in endpoints:
            sugestao = endpoints.get(nome_usado)
            print(f"Arquivo: {arquivo}")
            print(f"Linha {linha}: {conteudo}")
            if sugestao:
                print(f"  ➤ Sugestão: troque para url_for('{sugestao}')")
            else:
                print(f"  ⚠️ Endpoint '{nome_usado}' não encontrado no flask routes")
            print('-' * 60)

if __name__ == "__main__":
    main()
