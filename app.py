import openpyxl
from urllib.parse import quote
import webbrowser
import time
import pyautogui
import os
from datetime import datetime

confirmar_envio = True

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

def enviar_mensagem_whatsapp(numero, mensagem):
    global confirmar_envio

    try:
        mensagem_codificada = quote(mensagem)
        url = f'https://web.whatsapp.com/send?phone={numero}&text={mensagem_codificada}'
        
        webbrowser.open(url, new=2)
        time.sleep(10)
        
        botao_enviar = esperar_elemento('seta.png', timeout=15)

        # CONFIRMAÇÃO AVANÇADA
        if confirmar_envio:
            resposta = pyautogui.confirm(
                text=f"Pronto para enviar a mensagem para {numero}?\n\n{mensagem}",
                title='Confirmação de Envio',
                buttons=['Sim', 'Pular todos os próximos', 'Não']
            )
            if resposta == 'Pular todos os próximos':
                confirmar_envio = False
            elif resposta == 'Não':
                pyautogui.hotkey('ctrl', 'w')
                return False

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
        mensagem = (
            f"Olá {nome}, seu boleto vence no dia {data_formatada}. "
            "Favor pagar no link: https://www.link_do_pagamento.com"
        )
        
        sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
        
        if not sucesso:
            with open('erros.csv', 'a', encoding='utf-8') as arquivo:
                arquivo.write(f"{nome},{telefone}\n")
    
    print("Processo concluído. Verifique 'erros.csv' para falhas.")

if __name__ == "__main__":
    main()