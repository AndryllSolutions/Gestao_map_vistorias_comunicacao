import os

RAIZ = os.path.dirname(os.path.abspath(__file__))
ERROS_ENCONTRADOS = []

def eh_arquivo_invalido(filepath):
    return filepath.endswith('__init__.py') or not filepath.endswith('.py')

def verificar_linha(file_path, linha, n_linha):
    if 'SQLAlchemy()' in linha and '__init__.py' not in file_path:
        ERROS_ENCONTRADOS.append((file_path, n_linha, linha.strip()))

def escanear_projeto():
    for root, dirs, files in os.walk(RAIZ):
        for file in files:
            caminho = os.path.join(root, file)
            if eh_arquivo_invalido(caminho):
                continue

            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    for i, linha in enumerate(f, start=1):
                        verificar_linha(caminho, linha, i)
            except (UnicodeDecodeError, PermissionError):
                continue

def exibir_resultados():
    if not ERROS_ENCONTRADOS:
        print("✅ Nenhuma instância indevida de SQLAlchemy() encontrada!")
    else:
        print("🚨 Instâncias indevidas encontradas:")
        for arquivo, linha, conteudo in ERROS_ENCONTRADOS:
            print(f"📄 {arquivo} (linha {linha}): {conteudo}")

if __name__ == '__main__':
    print("🔍 Verificando instâncias de SQLAlchemy fora do __init__.py...")
    escanear_projeto()
    exibir_resultados()
