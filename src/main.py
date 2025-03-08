import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
import time
import traceback

from data.stock_data import get_stock_performance_data
from dashboard.ui import BrazilStocksDashboard

class LoadingScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Carregando...")
        self.master.geometry("500x400")
        self.master.resizable(True, True)
        
        frame = ttk.Frame(self.master, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Carregando dados das ações da B3...", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, 
                                        length=400, mode='determinate',
                                        variable=self.progress_var)
        self.progress.pack(pady=10)
        
        self.status_label = ttk.Label(frame, text="Preparando...")
        self.status_label.pack(pady=5)
        
        # Frame com scroll para os logs
        log_frame = ttk.Frame(frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=15, width=60, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.master.update()
        
    def update_progress(self, current, total):
        progress_pct = (current / total) * 100
        self.progress_var.set(progress_pct)
        self.status_label.config(text=f"Processando ação {current} de {total} ({progress_pct:.1f}%)")
        self.master.update()

def open_dashboard_with_data(performance_data):
    """
    Função específica para abrir o dashboard, garantindo que seja exibido mesmo com erros parciais
    """
    try:
        # Criar uma nova janela Tkinter para o dashboard
        dashboard_root = tk.Tk()
        # Criar o dashboard com os dados disponíveis
        app = BrazilStocksDashboard(dashboard_root, performance_data)
        # Iniciar o loop principal
        dashboard_root.mainloop()
    except Exception as e:
        # Se houver erro na criação do dashboard, mostrar uma mensagem
        error_msg = f"Erro ao criar dashboard: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        messagebox.showerror("Erro no Dashboard", 
                            f"Erro ao criar o dashboard: {str(e)}\n\nVerifique o console para mais detalhes.")

def load_data():
    """Carrega os dados em uma thread separada"""
    try:
        # Mostrar tela de carregamento
        root = tk.Tk()
        loading_screen = LoadingScreen(root)
        loading_screen.log("Iniciando carregamento de dados da B3...")
        
        # Iniciar thread para carregar dados
        def fetch_data_thread():
            performance_data = None
            try:
                # Obter dados de desempenho das ações
                performance_data = get_stock_performance_data(loading_screen)
                
                # Verificar se há dados disponíveis
                if performance_data is not None and not performance_data.empty:
                    # Contabilizar ações carregadas
                    n_stocks = len(performance_data)
                    loading_screen.log(f"Dados carregados com sucesso. {n_stocks} ações disponíveis.")
                    loading_screen.log("Abrindo dashboard...")
                    
                    # Garantir que a interface seja atualizada antes de fechá-la
                    root.update_idletasks()
                    
                    # Importante: Criar uma função para abrir o dashboard após fechar a tela de carregamento
                    root.after(1000, lambda: root.destroy())
                    
                    # Aqui está a mudança crítica: usamos after_idle para garantir que o dashboard abra após a tela de carregamento fechar
                    root.after_idle(lambda: open_dashboard_with_data(performance_data))
                else:
                    # Verificar se há dados disponíveis
                    loading_screen.log("ERRO: Nenhum dado foi carregado!")
                    messagebox.showerror("Erro", "Não foi possível carregar dados das ações.")
                    root.destroy()
            except Exception as e:
                error_msg = f"ERRO durante carregamento: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                loading_screen.log(error_msg)
                
                # Mesmo com erro, se temos pelo menos alguns dados, podemos mostrar o dashboard
                if performance_data is not None and not performance_data.empty:
                    loading_screen.log("Abrindo dashboard com dados parciais...")
                    root.after(2000, lambda: root.destroy())
                    root.after_idle(lambda: open_dashboard_with_data(performance_data))
                else:
                    messagebox.showerror("Erro", f"Falha ao carregar dados: {str(e)}")
                    root.destroy()
        
        # Iniciar thread para não bloquear a interface
        data_thread = threading.Thread(target=fetch_data_thread)
        data_thread.daemon = True
        data_thread.start()
        
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Falha ao iniciar aplicativo: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        messagebox.showerror("Erro Fatal", f"Falha ao iniciar o aplicativo: {str(e)}")

if __name__ == "__main__":
    load_data()