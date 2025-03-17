import openpyxl
from urllib.parse import quote
import webbrowser
from time import sleep
import pyautogui
import os 

def enviar_mensagem_whatsapp(nome, telefone, vencimento):
    mensagem = f'Olá {nome}, seu boleto vence no dia {vencimento.strftime("%d/%m/%Y")}.' \
                ' Favor pagar no link https://www.link_do_pagamento.com'
    try:
        link_mensagem_whatsapp = f'https://web.whatsapp.com/send?phone={telefone}&text={quote(mensagem)}'
        webbrowser.open(link_mensagem_whatsapp)
        sleep(10)
        seta = pyautogui.locateCenterOnScreen('seta.png')
        sleep(2)
        pyautogui.click(seta[0], seta[1])
        sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        sleep(2)
    except:
        print(f'Não foi possível enviar mensagem para {nome}')
        with open('erros.csv', 'a', newline='', encoding='utf-8') as arquivo:
            arquivo.write(f'{nome},{telefone}{os.linesep}')

# Abrir WhatsApp Web
webbrowser.open('https://web.whatsapp.com/')
sleep(30)

# Carregar a planilha
workbook = openpyxl.load_workbook('clientes.xlsx')
pagina_clientes = workbook['Sheet1']

# Iterar sobre os clientes
total_clientes = 0
for linha in pagina_clientes.iter_rows(min_row=2):
    nome = linha[0].value
    telefone = linha[1].value
    vencimento = linha[2].value
    enviar_mensagem_whatsapp(nome, telefone, vencimento)
    total_clientes += 1
    sleep(5)

print(f'Mensagens enviadas para {total_clientes} clientes.')
