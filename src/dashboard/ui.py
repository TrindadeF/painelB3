import os
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
        
        # Adicionar botão de limpar cache no frame de ações
        cache_frame = ttk.Frame(controls_frame)
        cache_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(cache_frame, text="Forçar Atualização de Dados", 
                  command=self.clear_data_cache).pack(side=tk.LEFT, padx=5)
        
        # Adicionar opção para limitar número de ações
        limit_frame = ttk.Frame(controls_frame)
        limit_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.limit_var = tk.BooleanVar(value=True)
        limit_check = ttk.Checkbutton(limit_frame, text="Mostrar apenas ações principais (melhor performance)", 
                                     variable=self.limit_var, command=self.toggle_stock_limit)
        limit_check.pack(side=tk.LEFT, padx=5)
        
        # Frame para tabela de ações
        self.stocks_frame = ttk.LabelFrame(left_frame, text="Ações")
        self.stocks_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Usar a versão com rolagem em vez de paginação
        self.setup_scrollable_stock_table()
        
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
        """Cria área simples para exibição de gráficos"""
        # Texto de instruções
        ttk.Label(parent, 
                 text="Dê duplo clique em uma ação para ver sua rentabilidade",
                 font=("Arial", 12)).pack(pady=10)
        
        # Frame para exibir gráficos
        self.chart_display = ttk.Frame(parent)
        self.chart_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mensagem inicial
        ttk.Label(self.chart_display, 
                 text="Selecione uma ação (duplo clique) para ver o gráfico de rentabilidade",
                 font=("Arial", 12)).pack(pady=50)

    def show_period_performance(self, period_column):
        """Mostra gráfico de rentabilidade para o período selecionado"""
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        # Obter dados filtrados
        filtered_data = self.get_filtered_data()
        
        # Aplicar filtro de performance se necessário
        perf_filter = self.performance_filter.get()
        if perf_filter == "Positivos":
            filtered_data = filtered_data[filtered_data[period_column] > 0]
        elif perf_filter == "Negativos":
            filtered_data = filtered_data[filtered_data[period_column] < 0]
        elif perf_filter == "Top 10":
            filtered_data = filtered_data.nlargest(10, period_column)
        elif perf_filter == "Bottom 10":
            filtered_data = filtered_data.nsmallest(10, period_column)
        elif perf_filter == "Top 20":
            filtered_data = filtered_data.nlargest(20, period_column)
        elif perf_filter == "Bottom 20":
            filtered_data = filtered_data.nsmallest(20, period_column)
        
        # Se não houver dados após filtro
        if filtered_data.empty:
            ttk.Label(self.chart_display, 
                     text="Nenhum dado disponível para o filtro selecionado",
                     font=("Arial", 12)).pack(pady=50)
            return
        
        # Aplicar ordenação
        sort_option = self.chart_sort.get()
        if sort_option == "Maior Rentabilidade":
            sorted_data = filtered_data.sort_values(by=period_column, ascending=False)
        elif sort_option == "Menor Rentabilidade":
            sorted_data = filtered_data.sort_values(by=period_column, ascending=True)
        else:  # Alfabética
            sorted_data = filtered_data.sort_values(by='code')
        
        # Criar figura para o gráfico
        fig = plt.Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Título baseado no período
        period_titles = {
            "daily_return": "Rentabilidade Diária",
            "monthly_return": "Rentabilidade Mensal",
            "quarterly_return": "Rentabilidade Trimestral",
            "yearly_return": "Rentabilidade Anual",
            "ytd_return": "Rentabilidade do Ano Atual (YTD)"
        }
        
        title = period_titles.get(period_column, "Rentabilidade")
        
        # Preparar dados para o gráfico
        tickers = sorted_data['code'].tolist()
        returns = sorted_data[period_column].tolist()
        
        # Cores com base no valor (positivo/negativo)
        colors = ['green' if x > 0 else 'red' for x in returns]
        
        # Criar barras
        bars = ax.bar(tickers, returns, color=colors, alpha=0.7)
        
        # Adicionar valores no topo das barras para melhor visualização
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height >= 0:
                va = 'bottom'
                offset = 0.3
            else:
                va = 'top'
                offset = -0.8
                
            # Evitar mostrar muitos valores quando há muitas barras
            if len(bars) <= 30:  
                ax.text(bar.get_x() + bar.get_width()/2., height + offset,
                       f'{returns[i]:.1f}%',
                       ha='center', va=va, rotation=90, fontsize=8)
        
        # Configurar eixos e títulos
        ax.set_title(title, fontsize=14)
        ax.set_ylabel('Rentabilidade (%)', fontsize=12)
        ax.set_xlabel('Ações', fontsize=12)
        
        # Rotacionar labels do eixo x para melhor visualização
        plt.setp(ax.get_xticklabels(), rotation=90, ha='center', fontsize=8)
        
        # Adicionar grade para facilitar a leitura
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Linha de zero para referência
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Colocar gráfico no frame
        canvas = FigureCanvasTkAgg(fig, master=self.chart_display)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Adicionar barra de ferramentas para navegação
        toolbar_frame = ttk.Frame(self.chart_display)
        toolbar_frame.pack(fill=tk.X, padx=5)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        # Adicionar estatísticas
        self.add_chart_statistics(period_column, filtered_data)

    def add_chart_statistics(self, period_column, data):
        """Adiciona estatísticas sobre o período selecionado"""
        stats_frame = ttk.LabelFrame(self.chart_display, text="Estatísticas")
        stats_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Calcular estatísticas
        total_stocks = len(data)
        positives = len(data[data[period_column] > 0])
        negatives = len(data[data[period_column] < 0])
        neutral = total_stocks - positives - negatives
        
        avg_return = data[period_column].mean()
        max_return = data[period_column].max()
        min_return = data[period_column].min()
        
        top_performer = data.loc[data[period_column].idxmax()]['code'] if not data.empty else "N/A"
        worst_performer = data.loc[data[period_column].idxmin()]['code'] if not data.empty else "N/A"
        
        # Criar grid para estatísticas
        ttk.Label(stats_frame, text=f"Total de Ações: {total_stocks}", font=("Arial", 9, "bold")).grid(
            row=0, column=0, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text=f"Positivas: {positives} ({positives/total_stocks*100:.1f}%)", 
                  foreground="green").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text=f"Negativas: {negatives} ({negatives/total_stocks*100:.1f}%)", 
                  foreground="red").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text=f"Média: {avg_return:.2f}%",
                  foreground="green" if avg_return > 0 else "red" if avg_return < 0 else "black").grid(
                      row=1, column=0, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text=f"Máximo: {max_return:.2f}% ({top_performer})",
                  foreground="green").grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(stats_frame, text=f"Mínimo: {min_return:.2f}% ({worst_performer})",
                  foreground="red").grid(row=1, column=2, padx=10, pady=5, sticky="w")

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
    
    def setup_scrollable_stock_table(self):
        """Versão otimizada da tabela de ações com rolagem"""
        # Usar um canvas maior para melhor desempenho
        table_container = ttk.Frame(self.stocks_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Criar canvas com scrollbar
        self.canvas = tk.Canvas(table_container, borderwidth=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.canvas.yview)
        
        # Frame dentro do canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configurações gerais do canvas
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empacotar os componentes
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar mouse wheel scrolling - mais suave
        self.bind_mousewheel(self.canvas)
        
        # Configura cabeçalhos
        self._setup_table_headers()
        
        # IMPORTANTE: Adicionar esta linha para garantir que a tabela seja populada
        self.populate_stock_table()
    
    def _on_frame_configure(self, event=None):
        """Configura a região de rolagem corretamente"""
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_mousewheel(self, widget):
        """Vincula eventos de rolagem do mouse ao widget, com tratamento para diferentes sistemas"""
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        widget.bind("<Button-4>", self._on_mousewheel)  # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel)  # Linux scroll down

    def _on_mousewheel(self, event):
        """Trata evento de rolagem do mouse"""
        if not hasattr(self, 'canvas'):
            return
            
        if event.num == 4 or event.num == 5:  # Linux
            delta = -1 if event.num == 5 else 1
        else:  # Windows
            delta = int(event.delta/120)
        
        self.canvas.yview_scroll(-delta, "units")

    def populate_stock_table(self):
        """Versão otimizada para preencher a tabela de ações"""
        # Limpar widgets existentes
        for widget in self.scrollable_frame.winfo_children()[1:]:  # Mantém os cabeçalhos
            widget.destroy()
        
        # Aplicar filtros aos dados
        filtered_data = self.get_filtered_data()
        
        # Limitar número máximo de ações exibidas para melhor performance
        MAX_DISPLAYED_STOCKS = 100  # Limitar a 100 ações na tabela
        
        if len(filtered_data) > MAX_DISPLAYED_STOCKS:
            if self.sort_column:
                sorted_data = filtered_data.sort_values(by=self.sort_column, ascending=self.sort_ascending).head(MAX_DISPLAYED_STOCKS)
            else:
                sorted_data = filtered_data.head(MAX_DISPLAYED_STOCKS)
                
            # Mostrar aviso
            ttk.Label(self.scrollable_frame, text=f"Mostrando apenas {MAX_DISPLAYED_STOCKS} de {len(filtered_data)} ações. Use filtros para refinar a busca.",
                     foreground="blue").grid(row=MAX_DISPLAYED_STOCKS+1, column=0, columnspan=13, padx=10, pady=5)
        else:
            if self.sort_column:
                sorted_data = filtered_data.sort_values(by=self.sort_column, ascending=self.sort_ascending)
            else:
                sorted_data = filtered_data.sort_values(by='code')
        
        # Usar batch para não travar a interface
        self._populate_table_batch(sorted_data, 0, 20)

    def _populate_table_batch(self, data, start_idx, batch_size):
        """Preenche a tabela em lotes para não travar a interface"""
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        
        for i, (_, row) in enumerate(batch.iterrows(), start_idx + 1):
            try:
                # Código existente para adicionar células...
                ticker = str(row['code']) if 'code' in row else "N/A"
                price = self.safe_get_value(row, 'current_price')
                
                # Criar e posicionar widgets como antes...
                ttk.Label(self.scrollable_frame, text=ticker).grid(row=i, column=0, padx=10, pady=2, sticky="w")
                # ...
                
            except Exception as e:
                print(f"Erro ao adicionar ação {i}: {e}")
        
        # Se ainda há mais dados para mostrar, agendar o próximo lote
        if end_idx < len(data):
            self.master.after(10, lambda: self._populate_table_batch(data, end_idx, batch_size))
        else:
            # Terminou, adicionar bindings
            self.add_selection_bindings()
            self.scrollable_frame.update_idletasks()

    def safe_get_value(self, row, column_name):
        """Extrai com segurança um valor numérico de uma linha do DataFrame"""
        try:
            if column_name in row:
                value = row[column_name]
                if isinstance(value, pd.Series):
                    return float(value.iloc[0])
                else:
                    return float(value)
            return 0.0
        except Exception:
            return 0.0

    def add_selection_bindings(self):
        """Adiciona eventos de clique para seleção de ações na tabela"""
        # Verificar quantas linhas existem no frame scrollable
        total_rows = self.scrollable_frame.grid_size()[1]
        
        for row in range(1, total_rows):
            # Para cada linha na tabela (exceto o cabeçalho)
            for col in range(self.scrollable_frame.grid_size()[0]):
                # Encontra o widget na posição atual
                widget = self.scrollable_frame.grid_slaves(row=row, column=col)
                if widget:
                    # Clique simples para selecionar/destacar a linha
                    widget[0].bind("<Button-1>", lambda e, r=row: self.select_stock_row(r))
                    # Duplo clique para mostrar o gráfico de rentabilidade
                    widget[0].bind("<Double-Button-1>", lambda e, r=row: self.toggle_stock_selection(r))

    def select_stock_row(self, row):
        """Destaca a linha selecionada"""
        # Resetar cores de todas as linhas
        for r in range(1, self.scrollable_frame.grid_size()[1]):
            for c in range(self.scrollable_frame.grid_size()[0]):
                widget = self.scrollable_frame.grid_slaves(row=r, column=c)
                if widget:
                    widget[0].configure(background=self.master.cget('bg'))
        
        # Destacar a linha selecionada
        for col in range(self.scrollable_frame.grid_size()[0]):
            widget = self.scrollable_frame.grid_slaves(row=row, column=col)
            if widget:
                widget[0].configure(background='#e0e0ff')  # Cor de destaque leve

    def toggle_stock_selection(self, row):
        """Mostra o gráfico de rentabilidade da ação selecionada com duplo clique"""
        # Obter o ticker da ação a partir da primeira coluna
        ticker_widget = self.scrollable_frame.grid_slaves(row=row, column=0)
        if ticker_widget:
            ticker = ticker_widget[0].cget('text')
            
            # Destacar a linha selecionada (resetar destaques primeiro)
            for r in range(1, self.scrollable_frame.grid_size()[1]):
                for c in range(self.scrollable_frame.grid_size()[0]):
                    widget = self.scrollable_frame.grid_slaves(row=r, column=c)
                    if widget:
                        widget[0].configure(background=self.master.cget('bg'))
            
            # Destacar linha da ação atual
            for col in range(self.scrollable_frame.grid_size()[0]):
                widget = self.scrollable_frame.grid_slaves(row=row, column=col)
                if widget:
                    widget[0].configure(background='#e0e0ff')  # Cor de destaque leve
            
            # Mostrar APENAS o gráfico de rentabilidade para a ação selecionada
            self.show_stock_performance(ticker)

    def show_stock_performance(self, ticker):
        """Mostra APENAS o gráfico de rentabilidade de uma ação"""
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        # Obter dados da ação
        stock_data = self.performance_data[self.performance_data['code'] == ticker]
        
        if stock_data.empty:
            ttk.Label(self.chart_display, 
                     text=f"Não foram encontrados dados para {ticker}",
                     font=("Arial", 12)).pack(pady=50)
            return
        
        # Mostrar título
        ttk.Label(self.chart_display, 
                 text=f"Rentabilidade da Ação: {ticker}",
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Criar figura para o gráfico
        fig = plt.Figure(figsize=(10, 6), dpi=100)
        
        # Criar subplot para as rentabilidades
        ax = fig.add_subplot(111)
        
        # Colunas de rentabilidade disponíveis e seus nomes amigáveis
        return_columns = {
            'daily_return': 'Diária',
            'weekly_return': 'Semanal', 
            'monthly_return': 'Mensal', 
            'quarterly_return': 'Trimestral', 
            'yearly_return': 'Anual', 
            'ytd_return': 'YTD'
        }
        
        # Filtrar apenas colunas disponíveis nos dados
        available_returns = [(col, label) for col, label in return_columns.items() 
                             if col in stock_data.columns]
        
        if not available_returns:
            ttk.Label(self.chart_display, 
                     text=f"Não foram encontrados dados de rentabilidade para {ticker}",
                     font=("Arial", 12)).pack(pady=50)
            return
        
        # Extrair valores e labels
        values = []
        labels = []
        colors = []
        
        for col, label in available_returns:
            try:
                value = float(stock_data[col].iloc[0])
                values.append(value)
                labels.append(label)
                colors.append('green' if value > 0 else 'red')
            except (ValueError, IndexError, KeyError) as e:
                print(f"Erro ao processar {col} para {ticker}: {e}")
        
        # Criar gráfico de barras
        bars = ax.bar(labels, values, color=colors, alpha=0.7)
        
        # Adicionar valores no topo das barras
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height >= 0:
                y_pos = height + 0.3
                va = 'bottom'
            else:
                y_pos = height - 0.3
                va = 'top'
            
            ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                   f'{values[i]:.2f}%', ha='center', va=va)
        
        # Configurar eixos e títulos
        ax.set_title(f"Rentabilidade de {ticker}", fontsize=14)
        ax.set_ylabel('Rentabilidade (%)', fontsize=12)
        
        # Adicionar grid para facilitar a leitura
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Linha de zero para referência
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Ajustar layout
        fig.tight_layout()
        
        # Colocar gráfico no frame
        canvas = FigureCanvasTkAgg(fig, master=self.chart_display)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Adicionar informações adicionais da ação
        info_frame = ttk.LabelFrame(self.chart_display, text="Informações da Ação")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Obter dados da ação para exibição
        price = self.safe_get_value(stock_data.iloc[0], 'current_price')
        open_price = self.safe_get_value(stock_data.iloc[0], 'open_price')
        high_price = self.safe_get_value(stock_data.iloc[0], 'high_price')
        low_price = self.safe_get_value(stock_data.iloc[0], 'low_price')
        close_price = self.safe_get_value(stock_data.iloc[0], 'close_price')
        volume = self.safe_get_value(stock_data.iloc[0], 'volume')
        
        # Dados do setor
        sector = stock_data['sector'].iloc[0] if 'sector' in stock_data.columns else "N/A"
        
        # Grid para informações
        ttk.Label(info_frame, text="Preço Atual:", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=f"R$ {price:.2f}").grid(row=0, column=1, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Abertura:", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=f"R$ {open_price:.2f}").grid(row=0, column=3, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Máxima:", font=("Arial", 9, "bold")).grid(row=1, column=0, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=f"R$ {high_price:.2f}").grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Mínima:", font=("Arial", 9, "bold")).grid(row=1, column=2, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=f"R$ {low_price:.2f}").grid(row=1, column=3, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Fechamento:", font=("Arial", 9, "bold")).grid(row=2, column=0, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=f"R$ {close_price:.2f}").grid(row=2, column=1, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Volume:", font=("Arial", 9, "bold")).grid(row=2, column=2, padx=10, pady=2, sticky="w")
        if volume >= 1_000_000:
            vol_text = f"R$ {volume/1_000_000:.2f}M"
        else:
            vol_text = f"R$ {volume/1_000:.2f}K" if volume > 0 else "R$ 0.00"
        ttk.Label(info_frame, text=vol_text).grid(row=2, column=3, padx=10, pady=2, sticky="w")
        
        ttk.Label(info_frame, text="Setor:", font=("Arial", 9, "bold")).grid(row=3, column=0, padx=10, pady=2, sticky="w")
        ttk.Label(info_frame, text=sector).grid(row=3, column=1, padx=10, pady=2, sticky="w", columnspan=3)

    def create_change_label(self, parent, value, row, column):
        """Cria um label formatado para mostrar variação percentual com cores"""
        if pd.isna(value):
            text = "N/A"
            color = "black"
        else:
            text = f"{value:.2f}%"
            color = "green" if value > 0 else "red" if value < 0 else "black"
        
        label = ttk.Label(parent, text=text, foreground=color)
        label.grid(row=row, column=column, padx=10, pady=2, sticky="e")
        return label

    def clear_data_cache(self):
        """Limpa o cache e reinicia o programa para carregar dados novos"""
        from data.stock_cache import StockDataCache
        
        if messagebox.askyesno("Atualizar dados", "Deseja forçar uma atualização dos dados?\nO programa será reiniciado."):
            try:
                cache = StockDataCache()
                cache.clear_cache()
                messagebox.showinfo("Cache limpo", "Cache removido. O programa será reiniciado para carregar dados atualizados.")
                
                # Reiniciar o programa
                self.master.destroy()
                
                # Iniciar uma nova instância do programa
                import sys
                import subprocess
                
                # Iniciar o processo python novamente com os mesmos argumentos
                subprocess.Popen([sys.executable] + sys.argv)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível limpar o cache: {str(e)}")

    def toggle_stock_limit(self):
        """Alterna entre mostrar todas as ações ou apenas as principais"""
        limit = self.limit_var.get()
        os.environ['LIMIT_STOCKS'] = str(limit)
        
        if messagebox.askyesno("Recarregar dados", 
                              "É necessário recarregar os dados para aplicar esta configuração. Deseja continuar?"):
            self.clear_data_cache()  # Reutiliza método existente para limpar cache e reiniciar

    # Adicione este método que está faltando para configurar os cabeçalhos da tabela
    def _setup_table_headers(self):
        """Configura os cabeçalhos da tabela de ações"""
        # Configura cabeçalhos da tabela com os campos necessários
        headers = ["Ação", "Preço", "Abertura", "Mínima", "Máxima", "Fechamento", "Vol. Financeiro", "Vol. Negócios", "Var %", "Var 1M %", "Var 3M %", "Var 12M %", "Var YTD %"]
        for col, header in enumerate(headers):
            ttk.Label(self.scrollable_frame, text=header, font=("Arial", 10, "bold")).grid(
                row=0, column=col, padx=10, pady=5, sticky="w"
            )

    # Substitua o método de população da tabela por uma versão que garanta que todas as ações sejam exibidas
    def populate_stock_table(self):
        """Preenche a tabela com todas as ações - versão corrigida"""
        # Limpar widgets existentes exceto cabeçalhos
        for widget in self.scrollable_frame.winfo_children():
            if int(widget.grid_info()['row']) > 0:  # Preservar cabeçalhos (linha 0)
                widget.destroy()
        
        # Obter todos os dados, sem filtros iniciais
        all_data = self.performance_data
        
        # Verificar se há dados
        if all_data.empty:
            ttk.Label(self.scrollable_frame, text="Nenhum dado disponível", font=("Arial", 12)).grid(
                row=1, column=0, padx=10, pady=10, columnspan=13)
            return
        
        print(f"Total de ações disponíveis: {len(all_data)}")
        
        # Ordenar por código para facilitar localização
        sorted_data = all_data.sort_values(by='code')
        
        # Processar em lotes para melhor desempenho
        self._populate_table_batch(sorted_data, 0, 50)  # Aumentar tamanho do lote para 50

    def _populate_table_batch(self, data, start_idx, batch_size):
        """Preenche a tabela em lotes para não travar a interface"""
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        
        for i, (_, row) in enumerate(batch.iterrows(), start_idx + 1):
            try:
                # Obter dados básicos
                ticker = str(row['code']) if 'code' in row else "N/A"
                
                # Obter valores com segurança
                price = self.safe_get_value(row, 'current_price')
                open_price = self.safe_get_value(row, 'open_price') or self.safe_get_value(row, 'open')
                low_price = self.safe_get_value(row, 'low_price') or self.safe_get_value(row, 'low')
                high_price = self.safe_get_value(row, 'high_price') or self.safe_get_value(row, 'high')
                close_price = self.safe_get_value(row, 'close_price') or self.safe_get_value(row, 'close')
                
                financial_volume = self.safe_get_value(row, 'financial_volume') or self.safe_get_value(row, 'volume')
                trades_volume = self.safe_get_value(row, 'trades_volume') or self.safe_get_value(row, 'trades')
                
                # Retornos
                daily_change = self.safe_get_value(row, 'daily_return')
                monthly_change = self.safe_get_value(row, 'monthly_return')
                quarterly_change = self.safe_get_value(row, 'quarterly_return')
                yearly_change = self.safe_get_value(row, 'yearly_return')
                ytd_change = self.safe_get_value(row, 'ytd_return')
                
                # Adicionar cada célula à tabela
                ttk.Label(self.scrollable_frame, text=ticker).grid(row=i, column=0, padx=10, pady=2, sticky="w")
                ttk.Label(self.scrollable_frame, text=f"R$ {price:.2f}").grid(row=i, column=1, padx=10, pady=2, sticky="e")
                
                # Novos campos
                ttk.Label(self.scrollable_frame, text=f"R$ {open_price:.2f}").grid(row=i, column=2, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {low_price:.2f}").grid(row=i, column=3, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {high_price:.2f}").grid(row=i, column=4, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {close_price:.2f}").grid(row=i, column=5, padx=10, pady=2, sticky="e")
                
                # Formatação para volumes em milhões/milhares
                vol_text = f"R$ {financial_volume/1_000_000:.2f}M" if financial_volume >= 1_000_000 else \
                          f"R$ {financial_volume/1_000:.2f}K" if financial_volume > 0 else "R$ 0.00"
                
                ttk.Label(self.scrollable_frame, text=vol_text).grid(row=i, column=6, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"{trades_volume:,.0f}").grid(row=i, column=7, padx=10, pady=2, sticky="e")
                
                # Formatar as variações com cores
                self.create_change_label(self.scrollable_frame, daily_change, row=i, column=8)
                self.create_change_label(self.scrollable_frame, monthly_change, row=i, column=9)
                self.create_change_label(self.scrollable_frame, quarterly_change, row=i, column=10)
                self.create_change_label(self.scrollable_frame, yearly_change, row=i, column=11)
                self.create_change_label(self.scrollable_frame, ytd_change, row=i, column=12)
                
            except Exception as e:
                print(f"Erro ao adicionar ação {i} ({ticker if 'ticker' in locals() else 'desconhecida'}): {e}")
                continue
        
        # Se ainda há mais dados para mostrar, agendar o próximo lote
        if end_idx < len(data):
            self.master.after(10, lambda: self._populate_table_batch(data, end_idx, batch_size))
        else:
            # Terminou, adicionar bindings
            self.add_selection_bindings()
            self.scrollable_frame.update_idletasks()