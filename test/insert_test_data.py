# insert_test_data.py
import sqlite3
from datetime import datetime, timedelta

db = "database/atas.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

# Inserir uma ata de teste para a ala 1 (Criciuma1)
data_teste = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

# Inserir ata (sem criado_em)
cur.execute("""
    INSERT INTO atas (tipo, ala_id, data)
    VALUES (?, ?, ?)
""", ("sacramental", 1, data_teste))

ata_id = cur.lastrowid

# Inserir sacramental com tema
cur.execute("""
    INSERT INTO sacramental (ata_id, tema, discursantes)
    VALUES (?, ?, ?)
""", (ata_id, "A importância da Fé", '["João Silva", "Maria Santos"]'))

conn.commit()
conn.close()

print(f"✓ Ata de teste inserida! ID: {ata_id}")
print(f"  - Data: {data_teste}")
print(f"  - Tema: A importância da Fé")