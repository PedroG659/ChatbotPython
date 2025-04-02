import openpyxl
from urllib.parse import quote
import webbrowser
from time import sleep
import pyautogui
import os 

def validar_telefone(numero):

    numero = str(numero).replace(" ", "").replace("-", "")
    if not numero.startswith("+"):
        return "+55" + numero  
    return numero

def enviar_mensagem(nome, telefone, vencimento):

    telefone = validar_telefone(telefone)
    mensagem = f'Olá {nome}, seu boleto vence no dia {vencimento.strftime("%d/%m/%Y")}.'
    mensagem += ' Favor pagar no link https://www.link_do_pagamento.com'
    
    try:
        link = f'https://web.whatsapp.com/send?phone={telefone}&text={quote(mensagem)}'
        webbrowser.open(link)
        sleep(15)  
        
        seta = pyautogui.locateCenterOnScreen('seta.png', confidence=0.8)
        if seta:
            pyautogui.click(seta)
            sleep(3)
            pyautogui.hotkey('ctrl', 'w')
        else:
            raise Exception("Botão de envio não encontrado")
    except Exception as e:
        print(f'Erro ao enviar mensagem para {nome}: {e}')
        with open('erros.csv', 'a', newline='', encoding='utf-8') as arquivo:
            arquivo.write(f'{nome},{telefone}{os.linesep}')


webbrowser.open('https://web.whatsapp.com/')
sleep(35)  

workbook = openpyxl.load_workbook('clientes.xlsx')
pagina_clientes = workbook['Sheet1']

for linha in pagina_clientes.iter_rows(min_row=2, values_only=True):
    nome, telefone, vencimento = linha
    if nome and telefone and vencimento:
        enviar_mensagem(nome, telefone, vencimento)
    else:
        print(f'Erro: Dados inválidos para {nome}. Pulando...')

workbook.close()
print("Processo concluído!")