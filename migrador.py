import sqlite3
import openpyxl
from datetime import datetime

EXCEL_FILE = 'clientes.xlsx'
DB_NAME = 'clientes.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        data_vencimento TEXT NOT NULL,
        enviado INTEGER DEFAULT 0,
        data_envio TEXT,
        falha INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()

def importar_dados():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        planilha = workbook['Sheet1']
        
        total = 0
        importados = 0
        duplicados = 0
        
        for linha in planilha.iter_rows(min_row=2, values_only=True):
            total += 1
            
            nome = linha[0] if len(linha) > 0 else None
            telefone = str(linha[1]).strip() if len(linha) > 1 else None
            data_venc = linha[2] if len(linha) > 2 else None
            
            if not nome or not telefone or not data_venc:
                print(f"[AVISO] Linha {total+1} ignorada - dados incompletos")
                continue
            
            cursor.execute("SELECT 1 FROM clientes WHERE telefone = ?", (telefone,))
            if cursor.fetchone():
                duplicados += 1
                print(f"[AVISO] Telefone {telefone} já existe - ignorando duplicata")
                continue
            
            if isinstance(data_venc, datetime):
                data_formatada = data_venc.strftime('%Y-%m-%d')
            else:
                try:
                    data_formatada = datetime.strptime(str(data_venc), '%d/%m/%Y').strftime('%Y-%m-%d')
                except ValueError:
                    data_formatada = str(data_venc)
            
            cursor.execute("""
            INSERT INTO clientes (nome, telefone, data_vencimento)
            VALUES (?, ?, ?)
            """, (nome, telefone, data_formatada))
            
            importados += 1
        
        conn.commit()
        print(f"\nMigração concluída:")
        print(f"Total de registros na planilha: {total}")
        print(f"Registros importados: {importados}")
        print(f"Duplicados ignorados: {duplicados}")
        print(f"Registros com problemas: {total - importados - duplicados}")
        
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro durante a migração:")
        print(str(e))
    finally:
        if 'conn' in locals():
            conn.close()
        if 'workbook' in locals():
            workbook.close()

if __name__ == "__main__":
    print("=== Migrador Excel para SQLite ===")
    print("1. Inicializando banco de dados...")
    init_db()
    
    print("\n2. Iniciando importação de dados...")
    importar_dados()
    
    print("\nProcesso concluído. Verifique o banco de dados 'clientes.db'")