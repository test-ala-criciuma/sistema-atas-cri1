import sqlite3
import os

def diagnostico_completo():
    # 1. Localizar o arquivo do banco
    db_file = 'database.db' # Certifique-se que este arquivo está na mesma pasta
    if not os.path.exists(db_file):
        print(f"❌ Erro: O arquivo {db_file} não foi encontrado na pasta atual.")
        return

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("--- 1. VERIFICANDO TABELAS NO BANCO ---")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = [row[0] for row in cursor.fetchall()]
        print(f"Tabelas encontradas: {tabelas}")

        nome_tabela = 'sacramental'
        if nome_tabela not in tabelas:
            print(f"❌ Erro: A tabela '{nome_tabela}' não existe!")
            return

        print(f"\n--- 2. VERIFICANDO COLUNAS DA TABELA '{nome_tabela}' ---")
        cursor.execute(f"PRAGMA table_info({nome_tabela});")
        colunas = {row[1]: row[2] for row in cursor.fetchall()}
        for col, tipo in colunas.items():
            print(f"Coluna: {col} | Tipo: {tipo}")

        print("\n--- 3. VERIFICANDO DADOS DA ATA ID: 1 ---")
        # Buscamos a última ata ou a de ID 1
        res = cursor.execute(f"SELECT * FROM {nome_tabela} ORDER BY id DESC LIMIT 1").fetchone()

        if res:
            dados = dict(res)
            print(f"ID da Ata: {dados.get('ata_id')}")
            
            # Verificando os campos problemáticos
            campos_teste = [
                'desobrigacoes', 
                'apoios', 
                'confirmacoes_batismo', # Nome que você enviou antes
                'apoio_membros',        # Nome que você enviou antes
                'bencao_criancas'       # Nome que você enviou antes
            ]

            for c in campos_teste:
                valor = dados.get(c, "NÃO EXISTE ESSA COLUNA")
                print(f"Campo [{c}]: {valor}")
        else:
            print("❌ Nenhum dado encontrado na tabela.")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    diagnostico_completo()