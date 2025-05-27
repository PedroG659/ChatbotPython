import sqlite3
from urllib.parse import quote
import webbrowser
import time
import pyautogui
from datetime import datetime
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuração do banco de dados
DB_NAME = "clientes.db"

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir"""
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

def get_clientes_pendentes():
    """Retorna todos os clientes com mensagens não enviadas"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT nome, telefone, data_vencimento 
    FROM clientes 
    WHERE enviado = 0 AND falha = 0
    """)
    
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def marcar_enviado(telefone, sucesso):
    """Marca o cliente como enviado ou com falha"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if sucesso:
        cursor.execute("""
        UPDATE clientes 
        SET enviado = 1, data_envio = ?
        WHERE telefone = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), telefone))
    else:
        cursor.execute("""
        UPDATE clientes 
        SET falha = 1
        WHERE telefone = ?
        """, (telefone,))
    
    conn.commit()
    conn.close()

def gerar_mensagem_com_ia(nome, data_venc):
    prompt = (
        f"Crie uma mensagem educada e simpática para um cliente chamado {nome}, "
        f"lembrando que o boleto dele vence no dia {data_venc}. "
        "Use um tom informal e amigável."
    )
    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8,
        )
        return resposta['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Erro ao gerar mensagem com IA: {e}")
        return (
            f"Olá {nome}, seu boleto vence no dia {data_venc}. "
            "Favor pagar no link: https://www.link_do_pagamento.com"
        )

def esperar_elemento(imagem, timeout=30):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            elemento = pyautogui.locateCenterOnScreen(imagem, confidence=0.8)
            if elemento:
                return elemento
        except pyautogui.ImageNotFoundException:
            pass
        time.sleep(2)
    raise TimeoutError(f"Elemento {imagem} não encontrado em {timeout} segundos.")

def confirmacao_visual(nome, telefone, mensagem):
    confirmacao_texto = (
        f"📋 Confirmação de Envio\n\n"
        f"👤 Nome: {nome}\n"
        f"📞 Telefone: {telefone}\n\n"
        f"💬 Mensagem:\n{mensagem}\n\n"
        f"Deseja enviar esta mensagem?"
    )
    
    try:
        resposta = pyautogui.confirm(
            text=confirmacao_texto,
            title='Confirmação de Envio',
            buttons=['Enviar', 'Cancelar']
        )
        return resposta == 'Enviar'
    except Exception as e:
        print(f"Erro na confirmação visual: {e}")
        print("\n" + "="*50)
        print(confirmacao_texto)
        resposta = input("\nDigite 'S' para enviar ou qualquer tecla para cancelar: ")
        return resposta.lower() == 's'

def enviar_mensagem_whatsapp(numero, mensagem):
    try:
        mensagem_codificada = quote(mensagem)
        url = f'https://web.whatsapp.com/send?phone={numero}&text={mensagem_codificada}'
        
        webbrowser.open(url, new=2)
        time.sleep(10)
        
        botao_enviar = esperar_elemento('seta.png', timeout=15)
        pyautogui.click(botao_enviar)
        time.sleep(2)
        
        pyautogui.hotkey('ctrl', 'w')
        return True
    
    except Exception as e:
        print(f"Erro ao enviar mensagem para {numero}: {str(e)}")
        return False

def formatar_data(data):
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    elif isinstance(data, str):
        return data
    else:
        return "Data inválida"

def main():
    # Inicializa o banco de dados
    init_db()
    
    webbrowser.open('https://web.whatsapp.com/')
    print("Por favor, faça login no WhatsApp Web em 10 segundos...")
    time.sleep(10)
    
    clientes = get_clientes_pendentes()
    
    if not clientes:
        print("Nenhum cliente pendente encontrado no banco de dados.")
        return
    
    for nome, telefone, vencimento in clientes:
        if not nome or not telefone or not vencimento:
            print(f"Dados incompletos para o cliente: {nome}")
            continue
        
        data_formatada = formatar_data(vencimento)
        mensagem = gerar_mensagem_com_ia(nome, data_formatada)

        print(f"\nPreparando envio para {nome} ({telefone})...")
        
        if not confirmacao_visual(nome, telefone, mensagem):
            print(f"Envio para {nome} cancelado pelo usuário.")
            continue
        
        print(f"Enviando para {nome} ({telefone}): {mensagem}")
        sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
        marcar_enviado(telefone, sucesso)
        
    print("Processo concluído. Verifique o banco de dados para clientes com falha.")

if __name__ == "__main__":
    main()