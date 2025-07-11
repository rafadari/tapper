import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from queue import Queue
from threading import Semaphore
import random

# Configurações
BALCOES = 4
VIDAS_INICIAIS = 3
CHEGADA_INICIAL = 3
CHEGADA_MIN = 0.5
PONTOS_FASE = 10

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍻 Tapper Game Premium")
        self.setup_window()
        self.menu()

    def setup_window(self):
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TButton', font=('Arial', 12), padding=10)
        self.style.configure('Title.TLabel', font=('Arial', 36, 'bold'), 
                              background='#2c3e50', foreground='#f39c12')
        self.style.configure('Success.TButton', foreground='white', background='#27ae60')
        self.style.map('Success.TButton',
                       foreground=[('active', 'white'), ('disabled', 'gray')],
                       background=[('active', '#2ecc71'), ('disabled', '#7f8c8d')])
        self.style.configure('Danger.TButton', foreground='white', background='#e74c3c')
        self.style.map('Danger.TButton',
                       foreground=[('active', 'white'), ('disabled', 'gray')],
                       background=[('active', '#c0392b'), ('disabled', '#7f8c8d')])

    def menu(self):
        self.clear_window()

        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)

        title_frame = tk.Frame(main_frame, bg='#2c3e50')
        title_frame.pack(pady=20)

        title = tk.Label(title_frame, text="🍻 TAPPER GAME 🍻", 
                         font=('Arial', 36, 'bold'), 
                         fg='#f1c40f', bg='#2c3e50')
        title.pack()

        subtitle = tk.Label(title_frame, text="Serve os clientes antes que fiquem furiosos!", 
                            font=('Arial', 14), fg='#ecf0f1', bg='#2c3e50')
        subtitle.pack(pady=10)

        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=40)

        start_btn = ttk.Button(button_frame, text="INICIAR JOGO", 
                               command=self.start_game, style='Success.TButton')
        start_btn.pack(pady=15, ipadx=30, ipady=10)

        exit_btn = ttk.Button(button_frame, text="SAIR", 
                              command=self.root.quit, style='Danger.TButton')
        exit_btn.pack(pady=15, ipadx=30, ipady=10)

    def start_game(self):
        self.clear_window()
        self.game = Tapper(self)

    def game_over_screen(self, pontos):
        self.clear_window()

        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)

        title = tk.Label(main_frame, text="💀 FIM DE JOGO 💀", 
                         font=('Arial', 36, 'bold'), 
                         fg='#e74c3c', bg='#2c3e50')
        title.pack(pady=20)

        score = tk.Label(main_frame, text=f"Pontuação: {pontos}", 
                         font=('Arial', 24), fg='#f1c40f', bg='#2c3e50')
        score.pack(pady=30)

        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(pady=30)

        retry_btn = ttk.Button(button_frame, text="JOGAR NOVAMENTE", 
                               command=self.start_game, style='Success.TButton')
        retry_btn.pack(pady=15, ipadx=20, ipady=8)

        menu_btn = ttk.Button(button_frame, text="MENU PRINCIPAL", 
                              command=self.menu, style='Danger.TButton')
        menu_btn.pack(pady=15, ipadx=20, ipady=8)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


class Tapper(tk.Canvas):
    def __init__(self, app):
        super().__init__(app.root, width=800, height=600, highlightthickness=0)
        self.pack()
        self.app = app

        self.images = {}

        try:
            self.images['fundo'] = PhotoImage(file="fundo.png")
        except Exception as e:
            print("Erro ao carregar imagem de fundo:", e)
            self.images['fundo'] = None

        try:
            self.images['garcom'] = PhotoImage(file="garcom.png").subsample(9,9)
        except Exception as e:
            print("Erro ao carregar imagem do garçom:", e)
            self.images['garcom'] = None

        try:
            self.images['clientes'] = [
                PhotoImage(file="cliente1.png").subsample(5, 5),
                PhotoImage(file="cliente2.png").subsample(5, 5),
                PhotoImage(file="cliente3.png").subsample(5, 5),
                PhotoImage(file="cliente4.png").subsample(5, 5)
            ]
        except Exception as e:
            print("Erro ao carregar imagens de clientes:", e)
            self.images['clientes'] = []

        self.garcom_img = self.images['garcom']

        if self.images.get('fundo'):
            self.create_image(0, 0, anchor='nw', image=self.images['fundo'], tags='fundo')

        self.vidas = VIDAS_INICIAIS
        self.pontos = 0
        self.fase = 1
        self.chegada = CHEGADA_INICIAL
        self.balcao_ys = [150, 230, 310, 390]
        self.clientes = [[] for _ in range(BALCOES)]
        self.pos_garcom = 0

        self.create_ui_elements()
        self.create_garcom()

        self.bind_all("<Up>", self.mover_cima)
        self.bind_all("<Down>", self.mover_baixo)
        self.bind_all("<space>", self.atender)
        self.bind_all("<p>", self.toggle_pause)
        self.focus_set()

        self.locks = [Semaphore(1) for _ in range(BALCOES)]
        self.filas = [Queue() for _ in range(BALCOES)]
        self.rodando = True
        self.pausado = False
        self.lock_vidas = threading.Lock()

        for i in range(BALCOES):
            threading.Thread(target=self.gerar_clientes, args=(i,), daemon=True).start()

        self.desenhar()

    def create_ui_elements(self):
        self.create_rectangle(0, 0, 800, 70, fill='#34495e', outline='#2c3e50', width=3)
        self.text_pontos = self.create_text(650, 35, fill='white', 
                                            font=('Arial', 16, 'bold'),
                                            text=f'🍺 PONTOS: {self.pontos}')
        self.text_vidas = self.create_text(150, 35, fill='white', 
                                           font=('Arial', 16, 'bold'),
                                           text=f'❤️ VIDAS: {self.vidas}')
        self.text_fase = self.create_text(400, 35, fill='white', 
                                          font=('Arial', 16, 'bold'),
                                          text=f'⭐ FASE: {self.fase}')

        for y in self.balcao_ys:
            self.create_rectangle(100, y, 700, y + 25, fill='#8b4513',
                                   outline='#5d2906', width=3)
            self.create_line(100, y+12, 700, y+12, fill='#5d2906', width=1, dash=(5,3))

    def create_garcom(self):
        if self.garcom_img:
            y = self.balcao_ys[self.pos_garcom]
            self.create_image(50, y - 10, image=self.garcom_img, tags='garcom')

    def mover_cima(self, event):
        if not self.pausado and self.pos_garcom > 0:
            self.pos_garcom -= 1
            y = self.balcao_ys[self.pos_garcom]
            self.move_garcom(y)

    def mover_baixo(self, event):
        if not self.pausado and self.pos_garcom < BALCOES - 1:
            self.pos_garcom += 1
            y = self.balcao_ys[self.pos_garcom]
            self.move_garcom(y)

    def move_garcom(self, y):
        self.delete('garcom')
        if self.garcom_img:
            self.create_image(50, y - 10, image=self.garcom_img, tags='garcom')

    def atender(self, event):
        if self.pausado:
            return

        idx = self.pos_garcom
        with self.locks[idx]:
            if not self.filas[idx].empty():
                self.filas[idx].get()
                self.pontos += 1
                self.itemconfig(self.text_pontos, text=f'🍺 PONTOS: {self.pontos}')

                if self.clientes[idx]:
                    self.clientes[idx].pop(0)

                if self.pontos % PONTOS_FASE == 0:
                    self.fase += 1
                    self.chegada = max(CHEGADA_MIN, self.chegada - 0.5)
                    self.itemconfig(self.text_fase, text=f'⭐ FASE: {self.fase}')

    def gerar_clientes(self, idx):
        while self.rodando:
            time.sleep(random.uniform(1, self.chegada))
            if self.pausado:
                continue

            with self.locks[idx]:
                if self.filas[idx].qsize() < 5:
                    self.filas[idx].put('cliente')
                    tipo = random.randint(0, 3)
                    self.clientes[idx].append(tipo)
                else:
                    with self.lock_vidas:
                        self.vidas -= 1
                        self.after(0, lambda: self.itemconfig(self.text_vidas, text=f'❤️ VIDAS: {self.vidas}'))
                        if self.vidas <= 0:
                            self.rodando = False
                            self.after(500, lambda: self.app.game_over_screen(self.pontos))
                            return

    def desenhar(self):
        self.delete('cliente')
        for i, clients in enumerate(self.clientes):
            for j, tipo in enumerate(clients):
                x = 150 + j * 60
                y = self.balcao_ys[i]
                if 'clientes' in self.images and 0 <= tipo < len(self.images['clientes']):
                    self.create_image(x, y - 25, image=self.images['clientes'][tipo], tags='cliente')

        if self.vidas > 0:
            self.after(150, self.desenhar)

    def toggle_pause(self, event=None):
        if not self.pausado:
            self.pausado = True
            self.mostrar_pausa()
        else:
            self.pausado = False
            self.ocultar_pausa()
            self.focus_set()

    def mostrar_pausa(self):
        self.pause_window = tk.Toplevel(self)
        self.pause_window.title("Jogo Pausado")
        self.pause_window.geometry("400x300")
        self.pause_window.configure(bg='#34495e')
        self.pause_window.grab_set()

        label = tk.Label(self.pause_window, text="⏸️ JOGO PAUSADO ⏸️", 
                         font=('Arial', 20, 'bold'), fg='#ecf0f1', bg='#34495e')
        label.pack(pady=30)

        btn_frame = tk.Frame(self.pause_window, bg='#34495e')
        btn_frame.pack()

        btn_continuar = ttk.Button(btn_frame, text="CONTINUAR", 
                                   command=self.toggle_pause, style='Success.TButton')
        btn_continuar.pack(pady=10, ipadx=20, ipady=5, fill='x')

        btn_menu = ttk.Button(btn_frame, text="MENU PRINCIPAL", 
                              command=self.voltar_menu, style='Danger.TButton')
        btn_menu.pack(pady=10, ipadx=20, ipady=5, fill='x')

    def ocultar_pausa(self):
        if hasattr(self, 'pause_window'):
            self.pause_window.destroy()

    def voltar_menu(self):
        self.rodando = False
        self.pausado = False
        self.ocultar_pausa()
        self.app.menu()

def main():
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
