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

# Semáforos e filas
locks = [Semaphore(1) for _ in range(BALCOES)]

# Filas de clientes
filas = [Queue() for _ in range(BALCOES)]

# Jogo
class Tapper(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, width=500, height=400, bg='darkgreen')
        self.pack()
        
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
        self.pos_garcom = 0  # 0 corresponde ao primeiro balcão
        self.bind("<Up>", self.mover_cima)
        self.bind("<Down>", self.mover_baixo)
        self.bind("<s pace>", self.atender)
        self.focus_set()

        # Inicia as threads de chegada de clientes
        for i in range(BALCOES):
            threading.Thread(target=self.gerar_clientes, args=(i,), daemon=True).start()

        self.desenhar()
    
    def create_balcao(self):
        for y in self.balcao_ys:
            self.create_rectangle(50, y, 450, y + 20, fill='saddlebrown')

    def mover_cima(self, event):
        if self.pos_garcom > 0:
            self.pos_garcom -= 1
            y = self.balcao_ys[self.pos_garcom]
            self.coords(self.garcom, 30, y - 10, 50, y + 10)

    def mover_baixo(self, event):
        if self.pos_garcom < BALCOES - 1:
            self.pos_garcom += 1
            y = self.balcao_ys[self.pos_garcom]
            self.coords(self.garcom, 30, y - 10, 50, y + 10)

    def atender(self, event):
        """Atende o balcão onde o garçom está posicionado."""
        idx = self.pos_garcom
        with locks[idx]:
            if not filas[idx].empty():
                filas[idx].get()
                self.pontos += 1
                self.itemconfig(self.text_pontos, text=f'Pontos: {self.pontos}')
                
                if self.clientes[idx]:
                    self.clientes[idx].pop(0)

                if self.pontos % PONTOS_FASE == 0:
                    self.fase += 1
                    self.itemconfig(self.text_fase, text=f'Fase: {self.fase}')
                    self.chegada = max(CHEGADA_MIN, self.chegada - 0.5)

    def gerar_clientes(self, idx):
        """Thread pra gerar clientes automaticamente."""
        while self.vidas > 0:
            time.sleep(random.uniform(1, self.chegada))
            with locks[idx]:
                if filas[idx].qsize() < 5:
                    filas[idx].put('cliente')
                    self.clientes[idx].append('cliente')
                else:
                    self.vidas -= 1
                    self.itemconfig(self.text_vidas, text=f'Vidas: {self.vidas}')
                    if self.vidas <= 0:
                        self.game_over()
                        return
    
    def desenhar(self):
        """Atualiza a posição gráfica dos clientes."""
        self.delete('cliente')
        for i, clients in enumerate(self.clientes):
            for j, _ in enumerate(clients):
                x = 100 + j*50
                y = self.balcao_ys[i] - 20
                self.create_oval(x, y, x + 20, y + 20, fill='yellow', tags='cliente')
        if self.vidas > 0:
            self.after(500, self.desenhar)

    def game_over(self):
        messagebox.showinfo("Fim de Jogo", f"Seu placar foi {self.pontos}")
        self.quit()


def main():
    root = tk.Tk()
    root.title("Tapper")
    game = Tapper(root)
    root.mainloop()


if __name__ == '__main__':
    main()
