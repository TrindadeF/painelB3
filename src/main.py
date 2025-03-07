import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
import time

from data.stock_data import get_stock_performance_data
from dashboard.ui import BrazilStocksDashboard

class LoadingScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Carregando...")
        self.master.geometry("300x150")
        self.master.resizable(False, False)
        
        frame = ttk.Frame(self.master, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Carregando dados das ações...", font=("Arial", 12)).pack(pady=10)
        
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
        self.progress.pack(pady=10)
        self.progress.start()

def load_data():
    """Carrega os dados em uma thread separada"""
    try:
        # Mostrar tela de carregamento
        root = tk.Tk()
        loading_screen = LoadingScreen(root)
        
        # Iniciar thread para carregar dados
        def fetch_data_thread():
            try:
                # Obter dados de desempenho das ações
                performance_data = get_stock_performance_data()
                
                # Fechar tela de carregamento
                root.after(1000, lambda: root.destroy())
                
                # Iniciar dashboard principal
                main_root = tk.Tk()
                app = BrazilStocksDashboard(main_root, performance_data)
                main_root.mainloop()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao carregar dados: {e}")
                root.destroy()
        
        # Iniciar thread para não bloquear a interface
        data_thread = threading.Thread(target=fetch_data_thread)
        data_thread.daemon = True
        data_thread.start()
        
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao iniciar o aplicativo: {e}")

if __name__ == "__main__":
    load_data()