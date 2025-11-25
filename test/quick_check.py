# quick_check.py
import sqlite3, os, datetime
db = os.path.join("database","atas.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
print("DB:", db)
print("Últimas 50 linhas com tema não vazio:")
for row in cur.execute("""SELECT a.id, a.data, a.ala_id, s.tema 
                          FROM sacramental s 
                          JOIN atas a ON s.ata_id=a.id 
                          WHERE s.tema IS NOT NULL AND TRIM(s.tema) <> '' 
                          ORDER BY a.data DESC LIMIT 50"""):
    print(row)
# Verificar quantos nos últimos 90 dias para a sua ala (alterar ala_id se precisar)
ninety_days = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
print("\nContagem desde", ninety_days)
cnt = cur.execute("""SELECT COUNT(*) FROM sacramental s JOIN atas a ON s.ata_id=a.id
                     WHERE date(a.data) >= date(?) AND s.tema IS NOT NULL AND TRIM(s.tema) <> '' AND a.ala_id = ?""",
                  (ninety_days, 1)).fetchone()[0]
print("count:", cnt)
conn.close()