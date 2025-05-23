import openpyxl
from urllib.parse import quote
import webbrowser
import time
import pyautogui
from datetime import datetime
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

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

#BANCO DE DADOS------------------------------------------------------------------------------------------------------------------
def conectar_banco():
    return psycopg2.connect(  # Retorna o objeto de conexão com os parâmetros abaixo
        dbname="chatbot",  # Nome do banco de dados
        user="postgres",  # Nome do usuário do banco
        password="postgres",  # Senha do usuário
        host="localhost",  # Endereço do servidor (localhost = máquina local)
        port="5432"  # Porta padrão do PostgreSQL
    )

# Define uma função chamada 'ler_clientes' que busca e retorna os dados dos clientes no banco
def ler_clientes():
    conexao = conectar_banco()  # Chama a função de conexão e guarda o objeto de conexão
    cursor = conexao.cursor()  # Cria um cursor para executar comandos SQL
    cursor.execute(  # Executa um comando SQL para selecionar dados da tabela 'clientes'
        "SELECT id, nome, numero FROM clientes"
    )
    clientes = []  # Cria uma lista vazia que irá armazenar os dicionários com os dados dos clientes
    for row in cursor.fetchall():  # Itera sobre todas as linhas retornadas pela consulta
        cliente = {  # Cria um dicionário com os dados de cada cliente
            "nome": row[0],  # Nome do cliente
            "numero": row[1],  # Número de telefone
        }
        clientes.append(cliente)  # Adiciona o dicionário à lista de clientes
    cursor.close()  # Fecha o cursor
    conexao.close()  # Fecha a conexão com o banco de dados
    return clientes  # Retorna a lista de clientes

# Imprime no console o resultado da função 'ler_clientes', ou seja, a lista de dicionários com os dados dos clientes
print(ler_clientes())

#FIM BANCO DE DADOS----------------------------------------------------------------------------------------------------------------

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
    webbrowser.open('https://web.whatsapp.com/')
    print("Por favor, faça login no WhatsApp Web em 10 segundos...")
    time.sleep(10)
    
    try:
        workbook = openpyxl.load_workbook('clientes.xlsx')
        pagina_clientes = workbook['Sheet1']
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        return
    
    for linha in pagina_clientes.iter_rows(min_row=2):
        nome = linha[0].value
        telefone = str(linha[1].value).strip()
        vencimento = linha[2].value
        
        if not nome or not telefone or not vencimento:
            print(f"Dados incompletos para a linha: {linha[0].row}")
            continue
        
        data_formatada = formatar_data(vencimento)
        mensagem = gerar_mensagem_com_ia(nome, data_formatada)

        print(f"\nPreparando envio para {nome} ({telefone})...")
        
        if not confirmacao_visual(nome, telefone, mensagem):
            print(f"Envio para {nome} cancelado pelo usuário.")
            continue
        
        print(f"Enviando para {nome} ({telefone}): {mensagem}")
        sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
        
        if not sucesso:
            with open('erros.csv', 'a', encoding='utf-8') as arquivo:
                arquivo.write(f"{nome},{telefone}\n")

    print("Processo concluído. Verifique 'erros.csv' para falhas.")

if __name__ == "__main__":
    main()
