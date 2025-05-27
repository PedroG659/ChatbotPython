import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from datetime import datetime
import sqlite3
import os
import openai
import webbrowser
import time
import pyautogui
from urllib.parse import quote

# Assuming DB_NAME, openai.api_key are set as in your original script
DB_NAME = "clientes.db"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Re-include your existing functions here:
# init_db, get_clientes_pendentes, marcar_enviado,
# gerar_mensagem_com_ia, esperar_elemento, enviar_mensagem_whatsapp, formatar_data

# Placeholder for the original functions (you'd paste them here)
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

def get_clientes_pendentes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, telefone, data_vencimento FROM clientes WHERE enviado = 0 AND falha = 0")
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def marcar_enviado(telefone, sucesso):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if sucesso:
        cursor.execute("UPDATE clientes SET enviado = 1, data_envio = ? WHERE telefone = ?", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), telefone))
    else:
        cursor.execute("UPDATE clientes SET falha = 1 WHERE telefone = ?", (telefone,))
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

def enviar_mensagem_whatsapp(numero, mensagem):
    try:
        mensagem_codificada = quote(mensagem)
        url = f'https://web.whatsapp.com/send?phone={numero}&text={mensagem_codificada}'

        webbrowser.open(url, new=2)
        time.sleep(10) # Give WhatsApp Web time to load

        # This part requires 'seta.png' in the same directory as the script
        # Ensure 'seta.png' is a clear image of the WhatsApp send button
        try:
            botao_enviar = esperar_elemento('seta.png', timeout=15)
            pyautogui.click(botao_enviar)
            time.sleep(2) # Give time for the message to send
            pyautogui.hotkey('ctrl', 'w') # Close the tab
            return True
        except TimeoutError as e:
            messagebox.showerror("Erro de Automação", f"Não foi possível encontrar o botão de envio do WhatsApp: {e}")
            pyautogui.hotkey('ctrl', 'w') # Try to close the tab even on failure
            return False

    except Exception as e:
        messagebox.showerror("Erro ao Abrir WhatsApp", f"Erro ao enviar mensagem para {numero}: {str(e)}")
        return False

def formatar_data(data):
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    elif isinstance(data, str):
        # Basic validation/reformatting if needed, assuming 'YYYY-MM-DD' from DB
        try:
            return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            return data # Return as is if format doesn't match
    else:
        return "Data inválida"


class WhatsAppSenderApp:
    def __init__(self, master):
        self.master = master
        master.title("Automatizador de Mensagens WhatsApp")
        master.geometry("600x400") # Set window size

        # Configure grid
        master.grid_rowconfigure(0, weight=0)
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # Control Frame
        self.control_frame = tk.Frame(master)
        self.control_frame.grid(row=0, column=0, pady=10)

        self.btn_init_db = tk.Button(self.control_frame, text="Inicializar DB", command=self.init_database)
        self.btn_init_db.pack(side=tk.LEFT, padx=5)

        self.btn_add_client = tk.Button(self.control_frame, text="Adicionar Cliente", command=self.add_new_client)
        self.btn_add_client.pack(side=tk.LEFT, padx=5)

        self.btn_start_whatsapp = tk.Button(self.control_frame, text="Abrir WhatsApp Web", command=self.open_whatsapp_web)
        self.btn_start_whatsapp.pack(side=tk.LEFT, padx=5)

        self.btn_send_messages = tk.Button(self.control_frame, text="Iniciar Envio de Mensagens", command=self.send_all_pending_messages)
        self.btn_send_messages.pack(side=tk.LEFT, padx=5)

        # Log Area
        self.log_frame = tk.LabelFrame(master, text="Logs de Atividade")
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, state='disabled', width=70, height=15)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.log("Aplicação iniciada. Por favor, inicialize o banco de dados e adicione clientes.")
        init_db() # Ensure DB is initialized when app starts

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.yview(tk.END)
        self.log_text.config(state='disabled')
        self.master.update_idletasks() # Refresh GUI

    def init_database(self):
        init_db()
        self.log("Banco de dados inicializado/verificado.")

    def add_new_client(self):
        nome = simpledialog.askstring("Adicionar Cliente", "Nome do Cliente:", parent=self.master)
        if not nome: return
        telefone = simpledialog.askstring("Adicionar Cliente", "Telefone (com código do país, ex: 5511987654321):", parent=self.master)
        if not telefone: return
        data_vencimento = simpledialog.askstring("Adicionar Cliente", "Data de Vencimento (YYYY-MM-DD):", parent=self.master)
        if not data_vencimento: return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nome, telefone, data_vencimento, enviado, falha) VALUES (?, ?, ?, 0, 0)",
                           (nome, telefone, data_vencimento))
            conn.commit()
            conn.close()
            self.log(f"Cliente '{nome}' adicionado com sucesso.")
        except Exception as e:
            self.log(f"Erro ao adicionar cliente: {e}")
            messagebox.showerror("Erro", f"Erro ao adicionar cliente: {e}")

    def open_whatsapp_web(self):
        self.log("Abrindo WhatsApp Web. Por favor, faça login manualmente se necessário.")
        webbrowser.open('https://web.whatsapp.com/')
        messagebox.showinfo("WhatsApp Web", "Por favor, faça login no WhatsApp Web. Clique 'OK' quando estiver pronto.")
        self.log("WhatsApp Web pronto para uso (presumindo login).")

    def send_all_pending_messages(self):
        self.log("Iniciando processo de envio de mensagens...")
        clientes = get_clientes_pendentes()

        if not clientes:
            self.log("Nenhum cliente pendente encontrado.")
            messagebox.showinfo("Envio Concluído", "Nenhum cliente pendente para enviar mensagens.")
            return

        self.log(f"Encontrados {len(clientes)} clientes pendentes.")

        for nome, telefone, vencimento in clientes:
            self.log(f"Processando cliente: {nome} ({telefone})")
            data_formatada = formatar_data(vencimento)
            mensagem = gerar_mensagem_com_ia(nome, data_formatada)

            # Use a Tkinter messagebox for visual confirmation
            confirmation_text = (
                f"Confirmação de Envio:\n\n"
                f"Nome: {nome}\n"
                f"Telefone: {telefone}\n\n"
                f"Mensagem:\n{mensagem}\n\n"
                f"Deseja enviar esta mensagem?"
            )

            if messagebox.askyesno("Confirmar Envio", confirmation_text):
                self.log(f"Enviando para {nome} ({telefone})...")
                sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
                marcar_enviado(telefone, sucesso)
                if sucesso:
                    self.log(f"Mensagem enviada com sucesso para {nome}.")
                else:
                    self.log(f"Falha ao enviar mensagem para {nome}. Marcado como falha.")
            else:
                self.log(f"Envio para {nome} ({telefone}) cancelado pelo usuário.")
                marcar_enviado(telefone, False) # Mark as failed if cancelled

        self.log("Processo de envio de mensagens concluído.")
        messagebox.showinfo("Envio Concluído", "Todas as mensagens pendentes foram processadas.")

if __name__ == "__main__":
    init_db() # Ensure DB is initialized before starting the app
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()