import shutil
from datetime import datetime

# Caminho do banco original e destino do backup
origem = 'database.db'
destino = f'backup_database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

shutil.copy2(origem, destino)
print(f"✅ Backup completo criado: {destino}")
