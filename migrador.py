import sqlite3
import openpyxl
from datetime import datetime

# Configurações
EXCEL_FILE = 'clientes.xlsx'
DB_NAME = 'clientes.db'

def init_db():
    """Inicializa o banco de dados com a estrutura correta"""
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
    """Importa dados do Excel para o banco de dados SQLite"""
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Abrir a planilha Excel
        workbook = openpyxl.load_workbook(EXCEL_FILE)
        planilha = workbook['Sheet1']  # Assumindo que os dados estão na Sheet1
        
        # Contadores para estatísticas
        total = 0
        importados = 0
        duplicados = 0
        
        # Percorrer as linhas da planilha (começando da linha 2)
        for linha in planilha.iter_rows(min_row=2, values_only=True):
            total += 1
            
            nome = linha[0] if len(linha) > 0 else None
            telefone = str(linha[1]).strip() if len(linha) > 1 else None
            data_venc = linha[2] if len(linha) > 2 else None
            
            # Validar dados básicos
            if not nome or not telefone or not data_venc:
                print(f"[AVISO] Linha {total+1} ignorada - dados incompletos")
                continue
            
            # Verificar se telefone já existe no banco
            cursor.execute("SELECT 1 FROM clientes WHERE telefone = ?", (telefone,))
            if cursor.fetchone():
                duplicados += 1
                print(f"[AVISO] Telefone {telefone} já existe - ignorando duplicata")
                continue
            
            # Formatar a data corretamente
            if isinstance(data_venc, datetime):
                data_formatada = data_venc.strftime('%Y-%m-%d')
            else:
                try:
                    # Tentar converter strings de data
                    data_formatada = datetime.strptime(str(data_venc), '%d/%m/%Y').strftime('%Y-%m-%d')
                except ValueError:
                    data_formatada = str(data_venc)
            
            # Inserir no banco de dados
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