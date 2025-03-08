import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

from .charts import create_comparison_chart, create_return_comparison_chart

class BrazilStocksDashboard:
    def __init__(self, master, performance_data):
        self.master = master
        self.performance_data = performance_data
        self.master.title("Dashboard de Ações Brasileiras - B3")
        self.master.geometry("1280x800")
        
        self.comparison_stocks = []  # Ações selecionadas para comparação
        self.filter_text = ""        # Texto para filtrar ações
        self.sort_column = ""        # Coluna atual de ordenação
        self.sort_ascending = True   # Direção da ordenação
        
        # Inicializar variáveis de paginação
        self.current_page = 0
        self.rows_per_page = 20
        
        # Criar um estilo personalizado para os cabeçalhos das colunas
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.create_widgets()
        
    def create_widgets(self):
        """Cria todos os widgets do dashboard"""
        # Frame principal com divisão em painéis
        main_paned = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Painel esquerdo para tabela de ações
        left_frame = ttk.Frame(main_paned, width=600)
        main_paned.add(left_frame, weight=1)
        
        # Painel direito para gráficos
        right_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(right_frame, weight=1)
        
        # Frame para filtros e controles
        controls_frame = ttk.LabelFrame(left_frame, text="Filtros e Controles")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Título principal
        ttk.Label(controls_frame, text="Dashboard de Ações da B3", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Frame para filtro de texto
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filtrar:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<Return>", lambda e: self.apply_filter())
        
        ttk.Button(filter_frame, text="Aplicar Filtro", command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Limpar Filtro", command=self.clear_filter).pack(side=tk.LEFT, padx=5)
        
        # Frame para filtro de setor
        sector_frame = ttk.Frame(controls_frame)
        sector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(sector_frame, text="Setor:").pack(side=tk.LEFT, padx=(0, 5))
        
        sectors = ['Todos'] + sorted(self.performance_data['sector'].unique().tolist())
        self.sector_var = tk.StringVar(value='Todos')
        sector_combobox = ttk.Combobox(sector_frame, textvariable=self.sector_var, values=sectors, width=25, state="readonly")
        sector_combobox.pack(side=tk.LEFT, padx=5)
        sector_combobox.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        
        # Frame para botões de ações
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Comparar Selecionadas", 
                  command=self.compare_selected_stocks).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Limpar Seleção", 
                  command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        
        # Frame para tabela de ações
        table_frame = ttk.LabelFrame(left_frame, text="Ações")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Agora criamos a tabela de ações
        self.create_stock_table(table_frame)
        
        # Frame para gráficos
        self.charts_frame = ttk.LabelFrame(right_frame, text="Gráficos e Comparativos")
        self.charts_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Inicializar área de gráficos
        self.create_charts_area(self.charts_frame)
        
    def create_stock_table(self, parent):
        """Cria a tabela de ações com paginação"""
        # Criar frame para tabela e scrollbar
        table_container = ttk.Frame(parent)
        table_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tabela de ações
        columns = ('code', 'sector', 'price', 'daily', 'weekly', 'monthly', 'yearly')
        self.stocks_table = ttk.Treeview(
            table_container, 
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            height=15
        )
        
        # Configurar cabeçalhos
        self.stocks_table.heading('code', text='Código', anchor=tk.W, 
                                  command=lambda: self.sort_by_column('code'))
        self.stocks_table.heading('sector', text='Setor', anchor=tk.W,
                                  command=lambda: self.sort_by_column('sector'))
        self.stocks_table.heading('price', text='Preço', anchor=tk.E,
                                  command=lambda: self.sort_by_column('current_price'))
        self.stocks_table.heading('daily', text='Diário', anchor=tk.E,
                                  command=lambda: self.sort_by_column('daily_return'))
        self.stocks_table.heading('weekly', text='Semanal', anchor=tk.E,
                                  command=lambda: self.sort_by_column('weekly_return'))
        self.stocks_table.heading('monthly', text='Mensal', anchor=tk.E,
                                  command=lambda: self.sort_by_column('monthly_return'))
        self.stocks_table.heading('yearly', text='Anual', anchor=tk.E,
                                  command=lambda: self.sort_by_column('yearly_return'))
        
        # Configurar colunas
        self.stocks_table.column('code', width=80, anchor=tk.W)
        self.stocks_table.column('sector', width=120, anchor=tk.W)
        self.stocks_table.column('price', width=80, anchor=tk.E)
        self.stocks_table.column('daily', width=80, anchor=tk.E)
        self.stocks_table.column('weekly', width=80, anchor=tk.E)
        self.stocks_table.column('monthly', width=80, anchor=tk.E)
        self.stocks_table.column('yearly', width=80, anchor=tk.E)
        
        # Configurar as tags para colorizar
        self.stocks_table.tag_configure('positive', background='#d4ffda')
        self.stocks_table.tag_configure('negative', background='#ffd4d4')
        self.stocks_table.tag_configure('selected', background='#d4d4ff')
        
        # Vincular scrollbars
        y_scrollbar.config(command=self.stocks_table.yview)
        x_scrollbar.config(command=self.stocks_table.xview)
        
        # Posicionar tabela
        self.stocks_table.pack(fill=tk.BOTH, expand=True)
        
        # Vincular eventos de seleção
        self.stocks_table.bind("<Double-1>", self.on_stock_selected)
        self.stocks_table.bind("<Return>", self.on_stock_selected)
        
        # Frame para paginação
        pagination_frame = ttk.Frame(parent)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botões de navegação
        nav_frame = ttk.Frame(pagination_frame)
        nav_frame.pack(pady=5)
        
        ttk.Button(nav_frame, text="<<", command=self.go_to_first_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="<", command=self.go_to_prev_page).pack(side=tk.LEFT, padx=2)
        
        # Inicializar self.page_label
        self.page_label = ttk.Label(nav_frame, text="Página 1 de 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(nav_frame, text=">", command=self.go_to_next_page).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text=">>", command=self.go_to_last_page).pack(side=tk.LEFT, padx=2)
        
        # Finalmente, carrega os dados na tabela
        self.load_stock_data()

    def create_charts_area(self, parent):
        """Cria a área para gráficos"""
        # Frame para instruções
        instructions = ttk.Frame(parent)
        instructions.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(instructions, 
                 text="Selecione ações na tabela (duplo clique) para adicionar aos comparativos.",
                 font=("Arial", 9)).pack(pady=5)
        
        # Frame para exibir gráficos
        self.chart_display = ttk.Frame(parent)
        self.chart_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mensagem inicial
        ttk.Label(self.chart_display, 
                 text="Selecione ações para ver comparativos",
                 font=("Arial", 12, "bold")).pack(pady=50)
    
    def on_stock_selected(self, event):
        """Adiciona ou remove uma ação da lista de comparação"""
        selection = self.stocks_table.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.stocks_table.item(item, 'values')
        stock_code = values[0]  # Código da ação está na primeira coluna
        
        # Toggle seleção
        if stock_code in self.comparison_stocks:
            self.comparison_stocks.remove(stock_code)
            self.stocks_table.item(item, tags=())  # Remove tag selecionada
        else:
            if len(self.comparison_stocks) >= 5:
                messagebox.showinfo("Limite atingido", "Você pode comparar até 5 ações simultaneamente.")
                return
            
            self.comparison_stocks.append(stock_code)
            
            # Adicionar tag visual para mostrar que está selecionada
            current_tags = list(self.stocks_table.item(item, "tags"))
            if 'positive' in current_tags:
                self.stocks_table.item(item, tags=('positive', 'selected'))
            elif 'negative' in current_tags:
                self.stocks_table.item(item, tags=('negative', 'selected'))
            else:
                self.stocks_table.item(item, tags=('selected',))
        
        # Atualizar status
        status = f"Ações selecionadas: {', '.join(self.comparison_stocks)}"
        print(status)  # Pode ser substituído por uma barra de status na UI
        
        # Se houver ações selecionadas, mostra botão de comparação
        if self.comparison_stocks:
            self.update_chart_preview()
    
    def update_chart_preview(self):
        """Mostra uma prévia do gráfico de comparação"""
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        if not self.comparison_stocks:
            ttk.Label(self.chart_display, 
                     text="Selecione ações para ver comparativos",
                     font=("Arial", 12, "bold")).pack(pady=50)
            return
        
        # Mostrar quais ações estão selecionadas
        selection_text = f"Ações selecionadas: {', '.join(self.comparison_stocks)}"
        ttk.Label(self.chart_display, text=selection_text).pack(pady=5)
        
        # Botão para gerar comparativo completo
        ttk.Button(self.chart_display, text="Gerar Comparativo Detalhado", 
                  command=self.compare_selected_stocks).pack(pady=10)
    
    def compare_selected_stocks(self):
        """Gera gráficos comparativos entre as ações selecionadas"""
        if not self.comparison_stocks:
            messagebox.showinfo("Sem seleção", "Selecione pelo menos uma ação para comparar.")
            return
        
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        # Criar notebook para diferentes tipos de comparação
        notebook = ttk.Notebook(self.chart_display)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab para preços
        price_tab = ttk.Frame(notebook)
        notebook.add(price_tab, text="Evolução de Preços")
        
        # Adicionar canvas com gráfico de preços
        price_chart = create_comparison_chart(self.comparison_stocks, price_tab)
        if price_chart:
            price_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Verificar quais colunas de retorno estão disponíveis
        columns = self.performance_data.columns.tolist()
        
        # Tab para retorno anual - usando o nome correto da coluna
        if 'yearly_return' in columns:
            annual_tab = ttk.Frame(notebook)
            notebook.add(annual_tab, text="Retorno Anual")
            
            annual_fig = create_return_comparison_chart(self.performance_data, 
                                                     self.comparison_stocks, 
                                                     'yearly_return')
            if annual_fig:
                annual_canvas = FigureCanvasTkAgg(annual_fig, annual_tab)
                annual_canvas.draw()
                annual_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
        # Tab para retorno mensal - usando o nome correto da coluna
        if 'monthly_return' in columns:
            monthly_tab = ttk.Frame(notebook)
            notebook.add(monthly_tab, text="Retorno Mensal")
            
            monthly_fig = create_return_comparison_chart(self.performance_data, 
                                                      self.comparison_stocks, 
                                                      'monthly_return')
            if monthly_fig:
                monthly_canvas = FigureCanvasTkAgg(monthly_fig, monthly_tab)
                monthly_canvas.draw()
                monthly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab para retorno semanal
        if 'weekly_return' in columns:
            weekly_tab = ttk.Frame(notebook)
            notebook.add(weekly_tab, text="Retorno Semanal")
            
            weekly_fig = create_return_comparison_chart(self.performance_data, 
                                                     self.comparison_stocks, 
                                                     'weekly_return')
            if weekly_fig:
                weekly_canvas = FigureCanvasTkAgg(weekly_fig, weekly_tab)
                weekly_canvas.draw()
                weekly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab para retorno diário
        if 'daily_return' in columns:
            daily_tab = ttk.Frame(notebook)
            notebook.add(daily_tab, text="Retorno Diário")
            
            daily_fig = create_return_comparison_chart(self.performance_data, 
                                                   self.comparison_stocks, 
                                                   'daily_return')
            if daily_fig:
                daily_canvas = FigureCanvasTkAgg(daily_fig, daily_tab)
                daily_canvas.draw()
                daily_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def load_stock_data(self):
        """Carrega os dados filtrados na tabela"""
        # Aplicar filtros
        filtered_data = self.get_filtered_data()
        
        # Limpar tabela atual
        for item in self.stocks_table.get_children():
            self.stocks_table.delete(item)
            
        # Calcular paginação
        total_rows = len(filtered_data)
        total_pages = max(1, (total_rows + self.rows_per_page - 1) // self.rows_per_page)
        
        # Ajustar página atual se necessário
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)
        
        # Selecionar dados para a página atual
        start_idx = self.current_page * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, total_rows)
        page_data = filtered_data.iloc[start_idx:end_idx]
        
        # Atualizar label de paginação se existir
        if hasattr(self, 'page_label'):
            self.page_label.config(text=f"Página {self.current_page + 1} de {total_pages}")
        
        # Preencher tabela
        for _, row in page_data.iterrows():
            try:
                # Extrair valores individuais corretamente:
                code = str(row['code']) if isinstance(row['code'], pd.Series) else str(row['code'])
                sector = str(row['sector']) if isinstance(row['sector'], pd.Series) else str(row['sector'])
                
                # Usar .iloc[0] para Series ou o valor direto para escalares
                price = float(row['current_price'].iloc[0]) if isinstance(row['current_price'], pd.Series) else float(row['current_price'])
                daily = float(row['daily_return'].iloc[0]) if isinstance(row['daily_return'], pd.Series) else float(row['daily_return'])
                weekly = float(row['weekly_return'].iloc[0]) if isinstance(row['weekly_return'], pd.Series) else float(row['weekly_return'])
                monthly = float(row['monthly_return'].iloc[0]) if isinstance(row['monthly_return'], pd.Series) else float(row['monthly_return'])
                yearly = float(row['yearly_return'].iloc[0]) if isinstance(row['yearly_return'], pd.Series) else float(row['yearly_return'])
                
                # Inserir na tabela com formatação apropriada
                item_id = self.stocks_table.insert(
                    "", 
                    "end", 
                    values=(
                        code,
                        sector,
                        f"R$ {price:.2f}",
                        f"{daily:.2f}%",
                        f"{weekly:.2f}%",
                        f"{monthly:.2f}%",
                        f"{yearly:.2f}%"
                    )
                )
                
                # Definir tags para colorização
                tags = []
                if code in self.comparison_stocks:
                    tags.append('selected')
                
                if daily > 0:
                    tags.append('positive')
                elif daily < 0:
                    tags.append('negative')
                    
                if tags:
                    self.stocks_table.item(item_id, tags=tuple(tags))
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                # Continuar para a próxima linha em caso de erro
                continue
    
    def get_filtered_data(self):
        """Retorna os dados filtrados com base nos critérios atuais"""
        data = self.performance_data.copy()
        
        # Aplicar filtro de texto se houver
        if self.filter_text:
            mask = data['code'].str.contains(self.filter_text, case=False)
            data = data[mask]
        
        # Aplicar filtro de setor se não for "Todos"
        if hasattr(self, 'sector_var') and self.sector_var.get() != 'Todos':
            data = data[data['sector'] == self.sector_var.get()]
        
        # Aplicar ordenação se definida
        if self.sort_column:
            data = data.sort_values(by=self.sort_column, ascending=self.sort_ascending)
        
        return data
    
    def sort_by_column(self, column_name):
        """Ordena os dados pela coluna especificada"""
        if self.sort_column == column_name:
            # Inverter direção se já estiver ordenando por esta coluna
            self.sort_ascending = not self.sort_ascending
        else:
            # Nova coluna: ordenar ascendente inicialmente, exceto para retornos
            if column_name in ['daily_return', 'weekly_return', 'monthly_return', 'yearly_return']:
                self.sort_ascending = False
            else:
                self.sort_ascending = True
                
        self.sort_column = column_name
        self.load_stock_data()
    
    def apply_filter(self):
        """Aplica o filtro atual aos dados"""
        self.filter_text = self.filter_entry.get().strip()
        self.current_page = 0  # Volta para primeira página
        self.load_stock_data()
    
    def clear_filter(self):
        """Limpa o filtro atual"""
        self.filter_text = ""
        self.filter_entry.delete(0, tk.END)
        self.sector_var.set("Todos")
        self.current_page = 0
        self.load_stock_data()
    
    def clear_selection(self):
        """Limpa a seleção de ações para comparação"""
        self.comparison_stocks = []
        self.load_stock_data()
        
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        ttk.Label(self.chart_display, 
                 text="Selecione ações para ver comparativos",
                 font=("Arial", 12, "bold")).pack(pady=50)
    
    def go_to_first_page(self):
        """Vai para a primeira página"""
        if self.current_page > 0:
            self.current_page = 0
            self.load_stock_data()
    
    def go_to_prev_page(self):
        """Vai para a página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_stock_data()
    
    def go_to_next_page(self):
        """Vai para a próxima página"""
        total_pages = (len(self.get_filtered_data()) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_stock_data()
    
    def go_to_last_page(self):
        """Vai para a última página"""
        total_pages = (len(self.get_filtered_data()) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page = total_pages - 1
            self.load_stock_data()