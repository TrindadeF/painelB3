import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .charts import create_comparison_chart, create_return_comparison_chart

class BrazilStocksDashboard:
    def __init__(self, master, performance_data):
        self.master = master
        self.performance_data = performance_data
        self.master.title("Dashboard de Ações Brasileiras")
        self.master.geometry("1200x800")
        
        self.comparison_stocks = []  # Ações selecionadas para comparação
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior para filtros
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Filtro por setor
        ttk.Label(filter_frame, text="Filtrar por Setor:").pack(side=tk.LEFT, padx=(0,5))
        self.sector_var = tk.StringVar()
        self.sector_var.set("Todos")
        
        # Obter lista única de setores
        sectors = ["Todos"] + list(self.performance_data["sector"].unique())
        
        sector_combo = ttk.Combobox(filter_frame, textvariable=self.sector_var, values=sectors)
        sector_combo.pack(side=tk.LEFT, padx=(0, 20))
        sector_combo.bind("<<ComboboxSelected>>", self.filter_stocks)
        
        # Botão para comparação
        ttk.Button(filter_frame, text="Comparar Selecionadas", command=self.compare_stocks).pack(side=tk.RIGHT)
        
        ttk.Button(filter_frame, text="Limpar Seleção", command=self.clear_selection).pack(side=tk.RIGHT, padx=10)
        
        # Frame para a tabela
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Criar tabela de ações
        self.create_stock_table(table_frame)
        
        # Frame para gráficos
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
    def create_stock_table(self, parent):
        columns = ("select", "sector", "code", "price", "daily", "weekly", "monthly", "yearly")
        
        self.stock_table = ttk.Treeview(
            parent, 
            columns=columns,
            show="headings", 
            selectmode="browse"
        )
        
        # Definir colunas
        self.stock_table.heading("select", text="", anchor=tk.CENTER)
        self.stock_table.heading("sector", text="Setor", anchor=tk.W)
        self.stock_table.heading("code", text="Código", anchor=tk.W)
        self.stock_table.heading("price", text="Preço Atual (R$)", anchor=tk.E)
        self.stock_table.heading("daily", text="Diário (%)", anchor=tk.E)
        self.stock_table.heading("weekly", text="Semanal (%)", anchor=tk.E)
        self.stock_table.heading("monthly", text="Mensal (%)", anchor=tk.E)
        self.stock_table.heading("yearly", text="Anual (%)", anchor=tk.E)
        
        # Definir larguras
        self.stock_table.column("select", width=30, stretch=False)
        self.stock_table.column("sector", width=100, stretch=True)
        self.stock_table.column("code", width=80, stretch=False)
        self.stock_table.column("price", width=100, stretch=False)
        self.stock_table.column("daily", width=80, stretch=False)
        self.stock_table.column("weekly", width=80, stretch=False)
        self.stock_table.column("monthly", width=80, stretch=False)
        self.stock_table.column("yearly", width=80, stretch=False)
        
        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.stock_table.yview)
        self.stock_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stock_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Vincular evento de duplo clique para selecionar ações para comparação
        self.stock_table.bind("<Double-1>", self.toggle_stock_selection)
        
        # Carregar os dados
        self.load_stock_data()
        
    def load_stock_data(self):
        # Limpar tabela
        for i in self.stock_table.get_children():
            self.stock_table.delete(i)
        
        # Formatar dados e adicionar à tabela
        for _, row in self.performance_data.iterrows():
            # Usar ✓ para stocks selecionados para comparação
            select_mark = "✓" if row['code'] in self.comparison_stocks else ""
            
            # Definir cores com base em valores positivos/negativos
            daily_val = f"{row['daily_return']:.2f}"
            weekly_val = f"{row['weekly_return']:.2f}"
            monthly_val = f"{row['monthly_return']:.2f}"
            yearly_val = f"{row['yearly_return']:.2f}"
            
            item_id = self.stock_table.insert("", "end", values=(
                select_mark,
                row['sector'],
                row['code'],
                f"{row['current_price']:.2f}",
                daily_val,
                weekly_val,
                monthly_val,
                yearly_val
            ))
            
            # Colorir linha de acordo com retorno anual
            if row['yearly_return'] > 0:
                self.stock_table.tag_configure('positive', background='#e6ffe6')
                self.stock_table.item(item_id, tags=('positive',))
            elif row['yearly_return'] < 0:
                self.stock_table.tag_configure('negative', background='#ffe6e6')
                self.stock_table.item(item_id, tags=('negative',))
    
    def filter_stocks(self, event=None):
        selected_sector = self.sector_var.get()
        
        if selected_sector == "Todos":
            filtered_data = self.performance_data
        else:
            filtered_data = self.performance_data[self.performance_data['sector'] == selected_sector]
        
        # Atualizar tabela com dados filtrados
        for i in self.stock_table.get_children():
            self.stock_table.delete(i)
        
        for _, row in filtered_data.iterrows():
            select_mark = "✓" if row['code'] in self.comparison_stocks else ""
            
            daily_val = f"{row['daily_return']:.2f}"
            weekly_val = f"{row['weekly_return']:.2f}"
            monthly_val = f"{row['monthly_return']:.2f}"
            yearly_val = f"{row['yearly_return']:.2f}"
            
            item_id = self.stock_table.insert("", "end", values=(
                select_mark,
                row['sector'],
                row['code'],
                f"{row['current_price']:.2f}",
                daily_val,
                weekly_val,
                monthly_val,
                yearly_val
            ))
            
            if row['yearly_return'] > 0:
                self.stock_table.tag_configure('positive', background='#e6ffe6')
                self.stock_table.item(item_id, tags=('positive',))
            elif row['yearly_return'] < 0:
                self.stock_table.tag_configure('negative', background='#ffe6e6')
                self.stock_table.item(item_id, tags=('negative',))
    
    def toggle_stock_selection(self, event):
        # Obter o item clicado
        item = self.stock_table.identify_row(event.y)
        if not item:
            return
            
        # Obter o código da ação
        stock_code = self.stock_table.item(item, "values")[2]
        
        # Adicionar/remover da lista de comparação
        if stock_code in self.comparison_stocks:
            self.comparison_stocks.remove(stock_code)
        else:
            if len(self.comparison_stocks) >= 5:  # Limite de 5 ações para comparação
                messagebox.showinfo("Limite atingido", "Você pode comparar até 5 ações.")
                return
            self.comparison_stocks.append(stock_code)
        
        # Atualizar a tabela
        self.filter_stocks()
    
    def compare_stocks(self):
        # Verificar se há ações selecionadas
        if not self.comparison_stocks:
            messagebox.showinfo("Seleção vazia", "Selecione ao menos uma ação para comparar.")
            return
        
        # Limpar o frame de gráficos
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Criar um notebook para diferentes gráficos
        notebook = ttk.Notebook(self.chart_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Criar abas para diferentes comparações
        price_tab = ttk.Frame(notebook)
        yearly_tab = ttk.Frame(notebook)
        monthly_tab = ttk.Frame(notebook)
        
        notebook.add(price_tab, text="Preço Normalizado")
        notebook.add(yearly_tab, text="Retorno Anual")
        notebook.add(monthly_tab, text="Retorno Mensal")
        
        # Gráfico de preço normalizado
        price_canvas = create_comparison_chart(self.comparison_stocks, price_tab)
        if price_canvas:
            price_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            toolbar = NavigationToolbar2Tk(price_canvas, price_tab)
            toolbar.update()
        
        # Gráfico de retorno anual
        yearly_fig = create_return_comparison_chart(
            self.performance_data, 
            self.comparison_stocks, 
            'yearly'
        )
        if yearly_fig:
            yearly_canvas = FigureCanvasTkAgg(yearly_fig, yearly_tab)
            yearly_canvas.draw()
            yearly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            yearly_toolbar = NavigationToolbar2Tk(yearly_canvas, yearly_tab)
            yearly_toolbar.update()
        
        # Gráfico de retorno mensal
        monthly_fig = create_return_comparison_chart(
            self.performance_data, 
            self.comparison_stocks, 
            'monthly'
        )
        if monthly_fig:
            monthly_canvas = FigureCanvasTkAgg(monthly_fig, monthly_tab)
            monthly_canvas.draw()
            monthly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            monthly_toolbar = NavigationToolbar2Tk(monthly_canvas, monthly_tab)
            monthly_toolbar.update()
    
    def clear_selection(self):
        self.comparison_stocks = []
        self.filter_stocks()
        
        # Limpar gráficos
        for widget in self.chart_frame.winfo_children():
            widget.destroy()