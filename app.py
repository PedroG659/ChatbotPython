import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk
from datetime import datetime
import sqlite3
import os
import openai
import webbrowser
import time
import pyautogui
from urllib.parse import quote
import re
import threading

DB_NAME = "clientes.db"

COR_PRIMARIA = "#2c3e50"
COR_SECUNDARIA = "#34495e"
COR_TERCIARIA = "#ecf0f1"
COR_BOTAO = "#3498db"
COR_BOTAO_HOVER = "#2980b9"
COR_SUCESSO = "#2ecc71"
COR_ERRO = "#e74c3c"
COR_AVISO = "#f39c12"

def configurar_estilo():
    estilo = ttk.Style()
    
    estilo.theme_use('clam')
    
    estilo.configure('TFrame', background=COR_TERCIARIA)
    estilo.configure('TLabel', background=COR_TERCIARIA, foreground=COR_PRIMARIA, font=('Segoe UI', 10))
    estilo.configure('TButton', background=COR_BOTAO, foreground='white', font=('Segoe UI', 10, 'bold'),
                    borderwidth=1, focusthickness=3, focuscolor=COR_BOTAO)
    estilo.map('TButton', background=[('active', COR_BOTAO_HOVER), ('pressed', COR_BOTAO_HOVER)])
    
    estilo.configure('TNotebook', background=COR_SECUNDARIA, borderwidth=0)
    estilo.configure('TNotebook.Tab', background=COR_SECUNDARIA, foreground='white',
                    padding=[15, 5], font=('Segoe UI', 10, 'bold'))
    estilo.map('TNotebook.Tab', background=[('selected', COR_PRIMARIA), ('active', COR_PRIMARIA)])
    
    estilo.configure('Treeview', background='white', fieldbackground='white', foreground=COR_PRIMARIA,
                    font=('Segoe UI', 9))
    estilo.configure('Treeview.Heading', background=COR_PRIMARIA, foreground='white',
                    font=('Segoe UI', 10, 'bold'))
    estilo.map('Treeview', background=[('selected', COR_BOTAO)])

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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_agendamento TEXT NOT NULL,
        hora_agendamento TEXT NOT NULL,
        criado_em TEXT NOT NULL,
        enviado INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()
    
    update_database_schema()

def update_database_schema():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(agendamentos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'enviado' not in columns:
            cursor.execute("ALTER TABLE agendamentos ADD COLUMN enviado INTEGER DEFAULT 0")
            conn.commit()
            print("Coluna 'enviado' adicionada à tabela agendamentos")
            
    except Exception as e:
        print(f"Erro ao atualizar schema: {e}")
    
    conn.close()

def get_clientes_pendentes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, telefone, data_vencimento FROM clientes WHERE enviado = 0 AND falha = 0")
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def get_todos_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, telefone, data_vencimento, enviado, data_envio, falha FROM clientes ORDER BY nome")
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def get_agendamentos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(agendamentos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'enviado' in columns:
        cursor.execute("SELECT id, nome, data_agendamento, hora_agendamento, enviado FROM agendamentos ORDER BY data_agendamento, hora_agendamento")
    else:
        cursor.execute("SELECT id, nome, data_agendamento, hora_agendamento, 0 as enviado FROM agendamentos ORDER BY data_agendamento, hora_agendamento")
    
    agendamentos = cursor.fetchall()
    conn.close()
    return agendamentos

def get_agendamentos_hoje():
    hoje = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(agendamentos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'enviado' in columns:
        cursor.execute("SELECT id, nome, data_agendamento, hora_agendamento FROM agendamentos WHERE data_agendamento = ? AND enviado = 0", (hoje,))
    else:
        cursor.execute("SELECT id, nome, data_agendamento, hora_agendamento FROM agendamentos WHERE data_agendamento = ?", (hoje,))
    
    agendamentos = cursor.fetchall()
    conn.close()
    return agendamentos

def marcar_enviado(telefone, sucesso):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if sucesso:
        cursor.execute("UPDATE clientes SET enviado = 1, data_envio = ? WHERE telefone = ?", 
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), telefone))
    else:
        cursor.execute("UPDATE clientes SET falha = 1 WHERE telefone = ?", (telefone,))
    conn.commit()
    conn.close()

def marcar_agendamento_enviado(agendamento_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(agendamentos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'enviado' in columns:
        cursor.execute("UPDATE agendamentos SET enviado = 1 WHERE id = ?", (agendamento_id,))
    
    conn.commit()
    conn.close()

def gerar_mensagem_com_ia(nome, data_venc):
    prompt = (
        f"Crie uma mensagem educada e simpática para um cliente chamado {nome}, "
        f"lembrando que o boleto dele vence no dia {data_venc}. "
        "Use um tom informal e amigável. Inclua emojis se apropriado."
    )
    try:
        if not openai.api_key:
            raise Exception("API key da OpenAI não configurada")
            
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

def gerar_mensagem_agendamento(nome, data, hora):
    prompt = (
        f"Crie uma mensagem educada e simpática para um cliente chamado {nome}, "
        f"lembrando que ele tem an agendamento marcado para o dia {data} às {hora}. "
        "Use um tom informal e amigável. Inclua emojis se apropriado."
    )
    try:
        if not openai.api_key:
            raise Exception("API key da OpenAI não configurada")
            
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
            f"Olá {nome}, lembramos que você tem um agendamento marcado para "
            f"{data} às {hora}. Esperamos por você!"
        )

def esperar_elemento(imagem, timeout=30):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            elemento = pyautogui.locateCenterOnScreen(imagem, confidence=0.8)
            if elemento:
                return elemento
        except (pyautogui.ImageNotFoundException, Exception):
            pass
        time.sleep(2)
    raise TimeoutError(f"Elemento {imagem} não encontrado em {timeout} segundos.")

def enviar_mensagem_whatsapp(numero, mensagem):
    try:
        mensagem_codificada = quote(mensagem)
        url = f'https://web.whatsapp.com/send?phone={numero}&text={mensagem_codificada}'

        webbrowser.open(url, new=2)
        time.sleep(10)

        try:
            botao_enviar = esperar_elemento('seta.png', timeout=15)
            pyautogui.click(botao_enviar)
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'w')
            return True
        except TimeoutError as e:
            messagebox.showwarning("Atenção", 
                f"Não foi possível encontrar o botão de envio automaticamente. "
                f"Por favor, envie a mensagem manualmente e feche a aba do WhatsApp.")
            time.sleep(10)
            pyautogui.hotkey('ctrl', 'w')
            return messagebox.askyesno("Confirmação", "A mensagem foi enviada com sucesso?")
    except Exception as e:
        messagebox.showerror("Erro ao Abrir WhatsApp", f"Erro ao enviar mensagem para {numero}: {str(e)}")
        return False

def formatar_data(data):
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    elif isinstance(data, str):
        try:
            return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            try:
                return datetime.strptime(data, '%d/%m/%Y').strftime('%d/%m/%Y')
            except ValueError:
                return data
    else:
        return "Data inválida"

def validar_telefone(telefone):
    return bool(re.fullmatch(r"\d{12,14}", telefone))

class BotaoEstilizado(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = self.cget('background')
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        self.config(background=COR_BOTAO_HOVER)
        
    def on_leave(self, e):
        self.config(background=self.default_bg)

class WhatsAppSenderApp:
    def __init__(self, master):
        self.master = master
        master.title("📱 Gerenciador de Clientes e Agendamentos")
        master.geometry("1000x700")
        master.minsize(900, 600)
        master.configure(bg=COR_TERCIARIA)
        
        configurar_estilo()

        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.user_response = None

        header_frame = ttk.Frame(master)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        titulo = tk.Label(header_frame, text="📱 WhatsApp Business Manager", 
                         font=('Segoe UI', 18, 'bold'), bg=COR_TERCIARIA, fg=COR_PRIMARIA)
        titulo.pack(pady=5)
        
        subtitulo = tk.Label(header_frame, text="Sistema de Gestão de Clientes e Envio de Mensagens", 
                            font=('Segoe UI', 10), bg=COR_TERCIARIA, fg=COR_SECUNDARIA)
        subtitulo.pack(pady=2)

        self.control_frame = ttk.Frame(master)
        self.control_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=20)
        self.control_frame.grid_columnconfigure(0, weight=1)

        button_frame = ttk.Frame(self.control_frame)
        button_frame.grid(row=0, column=0, pady=10)

        botoes_config = [
            ("🗄️", "Inicializar DB", self.init_database),
            ("👥", "Adicionar Cliente", self.add_new_client),
            ("📋", "Ver Clientes", self.view_clients),
            ("📅", "Adicionar Agendamento", self.add_new_appointment),
            ("💬", "Abrir WhatsApp Web", self.open_whatsapp_web),
            ("📤", "Iniciar Envio", self.send_all_pending_messages),
            ("🔔", "Verificar Agendamentos", self.check_todays_appointments)
        ]

        for icone, texto, comando in botoes_config:
            btn = BotaoEstilizado(button_frame, text=f" {icone} {texto}", command=comando,
                                bg=COR_BOTAO, fg='white', font=('Segoe UI', 10, 'bold'),
                                relief='flat', bd=0, padx=15, pady=8, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.notebook.configure(style='TNotebook')

        self.log_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.log_frame, text="📝 Logs do Sistema")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        log_container = ttk.Frame(self.log_frame, style='TFrame')
        log_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_container, wrap=tk.WORD, state='disabled', 
                                                width=85, height=20, font=('Consolas', 9),
                                                bg='white', fg=COR_PRIMARIA, relief='sunken', bd=2)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.appointment_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.appointment_frame, text="📅 Agendamentos")
        self.appointment_frame.grid_rowconfigure(0, weight=1)
        self.appointment_frame.grid_columnconfigure(0, weight=1)

        tree_container = ttk.Frame(self.appointment_frame, style='TFrame')
        tree_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        columns = ("Nome", "Data", "Hora", "Status")
        self.appointment_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.appointment_tree.heading(col, text=col)
            self.appointment_tree.column(col, width=180, anchor='center')
        
        self.appointment_tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.appointment_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.appointment_tree.configure(yscrollcommand=scrollbar.set)

        self.status_bar = tk.Label(master, text="Pronto | Sistema Inicializado", 
                                  relief='sunken', anchor='w', font=('Segoe UI', 9),
                                  bg=COR_PRIMARIA, fg='white')
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.log("🚀 Aplicação iniciada com sucesso!")
        self.log("💾 Banco de dados verificado e pronto para uso")
        self.log("👆 Use os botões acima para gerenciar clientes e agendamentos")
        init_db()
        self.update_appointment_tree()
        self.atualizar_status("Sistema carregado com sucesso | Pronto para operar")

    def log(self, message):
        self.log_text.config(state='normal')
        
        if "erro" in message.lower() or "falha" in message.lower():
            tag = "erro"
            self.log_text.tag_config(tag, foreground=COR_ERRO)
        elif "sucesso" in message.lower() or "✅" in message:
            tag = "sucesso"
            self.log_text.tag_config(tag, foreground=COR_SUCESSO)
        elif "⚠" in message or "atenção" in message.lower():
            tag = "aviso"
            self.log_text.tag_config(tag, foreground=COR_AVISO)
        else:
            tag = "normal"
            self.log_text.tag_config(tag, foreground=COR_PRIMARIA)
        
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n", tag)
        self.log_text.yview(tk.END)
        self.log_text.config(state='disabled')
        self.master.update_idletasks()

    def atualizar_status(self, mensagem):
        self.status_bar.config(text=f"🟢 {mensagem}")

    def update_appointment_tree(self):
        for item in self.appointment_tree.get_children():
            self.appointment_tree.delete(item)
            
        agendamentos = get_agendamentos()
        for ag_id, nome, data, hora, enviado in agendamentos:
            status = "✅ Enviado" if enviado else "⏳ Pendente"
            self.appointment_tree.insert("", "end", values=(nome, formatar_data(data), hora, status))

    def init_database(self):
        init_db()
        self.log("✅ Banco de dados inicializado/verificado com sucesso!")
        self.update_appointment_tree()
        self.atualizar_status("Banco de dados verificado")

    def add_new_client(self):
        self.atualizar_status("Adicionando novo cliente...")
        nome = simpledialog.askstring("Adicionar Cliente", "Nome do Cliente:", parent=self.master)
        if not nome:
            self.atualizar_status("Operação cancelada")
            return

        telefone = None
        while not telefone:
            telefone_input = simpledialog.askstring("Adicionar Cliente", "Telefone (com código do país, ex: 5511987654321):", parent=self.master)
            if telefone_input is None:
                self.atualizar_status("Operação cancelada")
                return
            if validar_telefone(telefone_input):
                telefone = telefone_input
            else:
                messagebox.showwarning("Telefone Inválido", "O número deve conter apenas dígitos e estar no formato internacional (ex: 5511987654321).")

        data_vencimento = simpledialog.askstring("Adicionar Cliente", "Data de Vencimento (YYYY-MM-DD):", parent=self.master)
        if not data_vencimento:
            self.atualizar_status("Operação cancelada")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nome, telefone, data_vencimento, enviado, falha) VALUES (?, ?, ?, 0, 0)",
                            (nome, telefone, data_vencimento))
            conn.commit()
            conn.close()
            self.log(f"✅ Cliente '{nome}' adicionado com sucesso!")
            self.atualizar_status(f"Cliente {nome} adicionado com sucesso")
        except Exception as e:
            self.log(f"❌ Erro ao adicionar cliente: {e}")
            messagebox.showerror("Erro", f"Erro ao adicionar cliente: {e}")
            self.atualizar_status("Erro ao adicionar cliente")
            
    def view_clients(self):
        self.atualizar_status("Carregando lista de clientes...")
        clientes = get_todos_clientes()
        
        client_window = tk.Toplevel(self.master)
        client_window.title("👥 Lista de Clientes")
        client_window.geometry("900x500")
        client_window.configure(bg=COR_TERCIARIA)
        client_window.transient(self.master)
        client_window.grab_set()
        
        header = tk.Label(client_window, text="📋 Lista de Clientes Cadastrados", 
                         font=('Segoe UI', 14, 'bold'), bg=COR_TERCIARIA, fg=COR_PRIMARIA)
        header.pack(pady=10)
        
        tree_frame = ttk.Frame(client_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        columns = ("ID", "Nome", "Telefone", "Vencimento", "Status", "Data Envio")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        
        tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        
        for cliente in clientes:
            id_cliente, nome, telefone, vencimento, enviado, data_envio, falha = cliente
            
            if falha:
                status = "❌ Falha"
            elif enviado:
                status = "✅ Enviado"
            else:
                status = "⏳ Pendente"
                
            tree.insert("", "end", values=(
                id_cliente, 
                nome, 
                telefone, 
                formatar_data(vencimento),
                status,
                data_envio if data_envio else "N/A"
            ))
        
        self.atualizar_status("Lista de clientes carregada")
            
    def add_new_appointment(self):
        self.atualizar_status("Adicionando novo agendamento...")
        nome = simpledialog.askstring("Adicionar Agendamento", "Nome do Cliente/Agendamento:", parent=self.master)
        if not nome:
            self.atualizar_status("Operação cancelada")
            return
            
        data_agendamento = simpledialog.askstring("Adicionar Agendamento", "Data (YYYY-MM-DD):", parent=self.master)
        if not data_agendamento:
            self.atualizar_status("Operação cancelada")
            return
            
        hora_agendamento = simpledialog.askstring("Adicionar Agendamento", "Hora (HH:MM):", parent=self.master)
        if not hora_agendamento:
            self.atualizar_status("Operação cancelada")
            return
            
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO agendamentos (nome, data_agendamento, hora_agendamento, criado_em) VALUES (?, ?, ?, ?)",
                            (nome, data_agendamento, hora_agendamento, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            self.log(f"✅ Agendamento para '{nome}' adicionado com sucesso!")
            self.update_appointment_tree()
            self.atualizar_status(f"Agendamento para {nome} adicionado")
        except Exception as e:
            self.log(f"❌ Erro ao adicionar agendamento: {e}")
            messagebox.showerror("Erro", f"Erro ao adicionar agendamento: {e}")
            self.atualizar_status("Erro ao adicionar agendamento")

    def open_whatsapp_web(self):
        self.log("🌐 Abrindo WhatsApp Web...")
        self.atualizar_status("Abrindo WhatsApp Web")
        webbrowser.open('https://web.whatsapp.com/')
        messagebox.showinfo("WhatsApp Web", "Por favor, faça login no WhatsApp Web. Clique 'OK' quando estiver pronto.")
        self.log("✅ WhatsApp Web pronto para uso!")
        self.atualizar_status("WhatsApp Web aberto - Pronto para enviar mensagens")

    def send_all_pending_messages(self):
        self.atualizar_status("Preparando envio de mensagens...")
        thread = threading.Thread(target=self._send_all_pending_messages_thread)
        thread.daemon = True
        thread.start()

    def _send_all_pending_messages_thread(self):
        self.log("📤 Iniciando processo de envio de mensagens...")
        self.atualizar_status("Processando mensagens pendentes")
        clientes = get_clientes_pendentes()

        if not clientes:
            self.log("ℹ️ Nenhum cliente pendente encontrado.")
            self.master.after(0, lambda: messagebox.showinfo("Envio Concluído", "Nenhum cliente pendente para enviar mensagens."))
            self.atualizar_status("Nenhuma mensagem pendente")
            return

        self.log(f"📊 Encontrados {len(clientes)} clientes pendentes.")
        self.atualizar_status(f"Processando {len(clientes)} mensagens")

        for nome, telefone, vencimento in clientes:
            self.log(f"🔍 Processando cliente: {nome} ({telefone})")
            data_formatada = formatar_data(vencimento)
            mensagem = gerar_mensagem_com_ia(nome, data_formatada)

            self.master.after(0, lambda n=nome, t=telefone, m=mensagem, d=data_formatada: self._ask_confirmation(n, t, m, d))
            
            while self.user_response is None:
                time.sleep(0.1)
                
            if self.user_response:
                self.log(f"✈️ Enviando para {nome} ({telefone})...")
                self.atualizar_status(f"Enviando para {nome}")
                sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
                marcar_enviado(telefone, sucesso)
                if sucesso:
                    self.log(f"✅ Mensagem enviada com sucesso para {nome}!")
                else:
                    self.log(f"❌ Falha ao enviar mensagem para {nome}.")
            else:
                self.log(f"⏸️ Envio para {nome} ({telefone}) cancelado pelo usuário.")
                marcar_enviado(telefone, False)
                
            self.user_response = None

        self.log("🎉 Processo de envio de mensagens concluído!")
        self.atualizar_status("Envio de mensagens concluído")
        self.master.after(0, lambda: messagebox.showinfo("Envio Concluído", "Todas as mensagens pendentes foram processadas."))

    def _ask_confirmation(self, nome, telefone, mensagem, data_formatada):
        confirmation_text = (
            f"📧 Confirmação de Envio:\n\n"
            f"👤 Nome: {nome}\n"
            f"📞 Telefone: {telefone}\n"
            f"📅 Vencimento: {data_formatada}\n\n"
            f"💬 Mensagem:\n{mensagem}\n\n"
            f"Deseja enviar esta mensagem?"
        )
        self.user_response = messagebox.askyesno("Confirmar Envio", confirmation_text)

    def check_todays_appointments(self):
        self.atualizar_status("Verificando agendamentos de hoje...")
        agendamentos = get_agendamentos_hoje()
        
        if not agendamentos:
            self.log("📅 Nenhum agendamento para hoje encontrado.")
            messagebox.showinfo("Agendamentos", "Nenhum agendamento para hoje.")
            self.atualizar_status("Nenhum agendamento para hoje")
            return
            
        self.log(f"📅 Encontrados {len(agendamentos)} agendamentos para hoje.")
        self.atualizar_status(f"{len(agendamentos)} agendamentos para hoje")
        
        for ag_id, nome, data, hora in agendamentos:
            mensagem = gerar_mensagem_agendamento(nome, formatar_data(data), hora)
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT telefone FROM clientes WHERE nome = ?", (nome,))
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                telefone = resultado[0]
                self.log(f"🔔 Enviando lembrete de agendamento para {nome} ({telefone})...")
                self.atualizar_status(f"Enviando lembrete para {nome}")
                
                confirmation_text = (
                    f"📅 Confirmação de Envio - Lembrete de Agendamento:\n\n"
                    f"👤 Nome: {nome}\n"
                    f"📞 Telefone: {telefone}\n"
                    f"⏰ Agendamento: {formatar_data(data)} às {hora}\n\n"
                    f"💬 Mensagem:\n{mensagem}\n\n"
                    f"Deseja enviar esta mensagem?"
                )
                
                if messagebox.askyesno("Confirmar Envio", confirmation_text):
                    sucesso = enviar_mensagem_whatsapp(telefone, mensagem)
                    if sucesso:
                        marcar_agendamento_enviado(ag_id)
                        self.log(f"✅ Lembrete de agendamento enviado com sucesso para {nome}!")
                    else:
                        self.log(f"❌ Falha ao enviar lembrete de agendamento para {nome}.")
                else:
                    self.log(f"⏸️ Envio de lembrete para {nome} cancelado pelo usuário.")
            else:
                self.log(f"⚠️ Cliente {nome} não encontrado na base de clientes.")
                
        self.update_appointment_tree()
        self.atualizar_status("Verificação de agendamentos concluída")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):

        pass
        
    init_db()
    root = tk.Tk()
    app = WhatsAppSenderApp(root)
    root.mainloop()