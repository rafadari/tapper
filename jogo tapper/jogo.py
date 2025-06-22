import threading
import time
import tkinter as tk
import random
from tkinter import messagebox
from queue import Queue
from threading import Semaphore

# Configurações
BALCOES = 4
VIDAS_INICIAIS = 3
CHEGADA_INICIAL = 3
CHEGADA_MIN = 0.5
PONTOS_FASE = 10


class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tapper")
        self.menu()

    def menu(self):
        self.clear_window()

        title = tk.Label(self.root, text="🍺 Tapper Game 🍺", font=("Arial", 24), bg='darkgreen', fg='white')
        title.pack(pady=40)

        start_button = tk.Button(self.root, text="Iniciar Jogo", font=("Arial", 16),
                                 command=self.start_game, width=20, bg='green', fg='white')
        start_button.pack(pady=10)

        exit_button = tk.Button(self.root, text="Sair", font=("Arial", 16),
                                command=self.root.quit, width=20, bg='red', fg='white')
        exit_button.pack(pady=10)

        self.root.configure(bg='darkgreen')

    def start_game(self):
        self.clear_window()
        self.game = Tapper(self)

    def game_over_screen(self, pontos):
        self.clear_window()

        label = tk.Label(self.root, text="💀 Fim de Jogo 💀", font=("Arial", 24), fg='red', bg='black')
        label.pack(pady=20)

        score_label = tk.Label(self.root, text=f"Seu placar foi: {pontos}", font=("Arial", 18), fg='white', bg='black')
        score_label.pack(pady=10)

        retry_button = tk.Button(self.root, text="Voltar ao Menu", font=("Arial", 14),
                                 command=self.menu, width=20, bg='gray', fg='white')
        retry_button.pack(pady=10)

        exit_button = tk.Button(self.root, text="Sair", font=("Arial", 14),
                                command=self.root.quit, width=20, bg='red', fg='white')
        exit_button.pack(pady=10)

        self.root.configure(bg='black')

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


class Tapper(tk.Canvas):
    def __init__(self, app):
        super().__init__(app.root, width=500, height=400, bg='darkgreen')
        self.pack()
        self.app = app

        self.vidas = VIDAS_INICIAIS
        self.pontos = 0
        self.fase = 1
        self.chegada = CHEGADA_INICIAL

        self.balcao_ys = [100, 160, 220, 280]
        self.clientes = [[] for _ in range(BALCOES)]

        self.text_pontos = self.create_text(400, 30, fill='white', text=f'Pontos: {self.pontos}')
        self.text_vidas = self.create_text(100, 30, fill='white', text=f'Vidas: {self.vidas}')
        self.text_fase = self.create_text(250, 30, fill='white', text=f'Fase: {self.fase}')

        self.create_balcao()
        self.garcom = self.create_rectangle(30, self.balcao_ys[0] - 10, 50, self.balcao_ys[0] + 10, fill='blue')
        self.pos_garcom = 0

        self.bind_all("<Up>", self.mover_cima)
        self.bind_all("<Down>", self.mover_baixo)
        self.bind_all("<space>", self.atender)
        self.bind_all("<p>", self.toggle_pause)

        self.focus_set()

        self.locks = [Semaphore(1) for _ in range(BALCOES)]
        self.filas = [Queue() for _ in range(BALCOES)]

        self.rodando = True
        self.pausado = False

        for i in range(BALCOES):
            threading.Thread(target=self.gerar_clientes, args=(i,), daemon=True).start()

        self.desenhar()

    def create_balcao(self):
        for y in self.balcao_ys:
            self.create_rectangle(50, y, 450, y + 20, fill='saddlebrown')

    def mover_cima(self, event):
        if not self.pausado and self.pos_garcom > 0:
            self.pos_garcom -= 1
            y = self.balcao_ys[self.pos_garcom]
            self.coords(self.garcom, 30, y - 10, 50, y + 10)

    def mover_baixo(self, event):
        if not self.pausado and self.pos_garcom < BALCOES - 1:
            self.pos_garcom += 1
            y = self.balcao_ys[self.pos_garcom]
            self.coords(self.garcom, 30, y - 10, 50, y + 10)

    def atender(self, event):
        if self.pausado:
            return
        idx = self.pos_garcom
        with self.locks[idx]:
            if not self.filas[idx].empty():
                self.filas[idx].get()
                self.pontos += 1
                self.itemconfig(self.text_pontos, text=f'Pontos: {self.pontos}')
                if self.clientes[idx]:
                    self.clientes[idx].pop(0)
                if self.pontos % PONTOS_FASE == 0:
                    self.fase += 1
                    self.itemconfig(self.text_fase, text=f'Fase: {self.fase}')
                    self.chegada = max(CHEGADA_MIN, self.chegada - 0.5)

    def gerar_clientes(self, idx):
        while self.rodando:
            time.sleep(random.uniform(1, self.chegada))
            if self.pausado:
                continue
            with self.locks[idx]:
                if self.filas[idx].qsize() < 5:
                    self.filas[idx].put('cliente')
                    self.clientes[idx].append('cliente')
                else:
                    self.vidas -= 1
                    self.itemconfig(self.text_vidas, text=f'Vidas: {self.vidas}')
                    if self.vidas <= 0:
                        self.rodando = False
                        self.after(500, lambda: self.app.game_over_screen(self.pontos))
                        return

    def desenhar(self):
        self.delete('cliente')
        for i, clients in enumerate(self.clientes):
            for j, _ in enumerate(clients):
                x = 100 + j * 50
                y = self.balcao_ys[i] - 20
                self.create_oval(x, y, x + 20, y + 20, fill='yellow', tags='cliente')
        if self.vidas > 0:
            self.after(500, self.desenhar)

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
        self.pause_window.title("Pausa")
        self.pause_window.geometry("300x250")
        self.pause_window.configure(bg='gray20')
        self.pause_window.grab_set()

        label = tk.Label(self.pause_window, text="⏸️ Jogo Pausado ⏸️", font=("Arial", 16), bg='gray20', fg='white')
        label.pack(pady=20)

        btn_continuar = tk.Button(self.pause_window, text="Continuar", width=20, bg='green', fg='white',
                                  command=self.toggle_pause)
        btn_continuar.pack(pady=5)

        btn_menu = tk.Button(self.pause_window, text="Voltar ao Menu", width=20, bg='gray', fg='white',
                             command=self.voltar_menu)
        btn_menu.pack(pady=5)

        btn_sair = tk.Button(self.pause_window, text="Encerrar Jogo", width=20, bg='red', fg='white',
                             command=self.app.root.quit)
        btn_sair.pack(pady=5)

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
