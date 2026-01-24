#!/usr/bin/env python3
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
# Use DB_PATH environment variable when provided (e.g., Railway with Persistent Disk)
DB_PATH = Path(os.environ.get('DB_PATH', str(BASE / 'database' / 'atas.db')))
SCHEMA_PATH = BASE / "database" / "schema_inicial.sql"
BACKUP_DIR = DB_PATH.parent / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if not SCHEMA_PATH.exists():
    print(f"ERRO: arquivo de schema não encontrado em {SCHEMA_PATH}")
    raise SystemExit(1)

if DB_PATH.exists():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"atas.db.bak.{ts}"
    shutil.copy2(DB_PATH, backup_file)
    print(f"Backup do DB existente criado em: {backup_file}")
    DB_PATH.unlink()
    print("Arquivo antigo removido.")

print("Criando novo banco a partir de schema_inicial.sql...")
sql = SCHEMA_PATH.read_text(encoding="utf-8")
conn = sqlite3.connect(DB_PATH)
conn.executescript(sql)
conn.close()
print("Banco criado com sucesso em:", DB_PATH)
print("Backups (se existirem) estão em:", BACKUP_DIR)