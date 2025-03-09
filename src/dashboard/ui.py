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
        for item in self.stocks_frame.get_children():
            self.stocks_frame.delete(item)
            
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
        """Retorna os dados filtrados com base nos critérios atuais - versão corrigida"""
        data = self.performance_data.copy()
        
        # Verificar valores válidos em 'code' para evitar erros
        if 'code' not in data.columns:
            print("Erro: coluna 'code' não encontrada nos dados")
            return data
        
        # Registrar o total de linhas antes da filtragem
        print(f"Total de linhas antes dos filtros: {len(data)}")
        
        # Aplicar filtro de texto se houver
        if self.filter_text:
            try:
                # Garantir que o código seja string para usar str.contains
                data['code'] = data['code'].astype(str)
                mask = data['code'].str.contains(self.filter_text, case=False, na=False)
                data = data[mask]
                print(f"Após filtro de texto '{self.filter_text}': {len(data)} linhas")
            except Exception as e:
                print(f"Erro ao filtrar por texto: {e}")
        
        # Aplicar filtro de setor se não for "Todos" - VERSÃO CORRIGIDA
        if hasattr(self, 'sector_var') and self.sector_var.get() != 'Todos':
            try:
                # Filtrar por setor selecionado (com tratamento de string)
                selected_sector = self.sector_var.get().strip()
                
                # Garantir que ambas as strings sejam comparadas corretamente
                if 'sector' in data.columns:
                    # Converter para string e normalizar
                    data['sector_norm'] = data['sector'].astype(str).str.strip()
                    
                    # Aplicar filtro e manter apenas linhas correspondentes
                    data = data[data['sector_norm'] == selected_sector]
                    
                    # Remover coluna temporária
                    if 'sector_norm' in data.columns:
                        data = data.drop('sector_norm', axis=1)
                    
                    print(f"Após filtro de setor '{selected_sector}': {len(data)} linhas")
                else:
                    print("Coluna 'sector' não encontrada nos dados")
            except Exception as e:
                print(f"Erro ao filtrar por setor: {e}")
                import traceback
                traceback.print_exc()
        
        # Aplicar ordenação se definida
        if self.sort_column and self.sort_column in data.columns:
            try:
                data = data.sort_values(by=self.sort_column, ascending=self.sort_ascending)
            except Exception as e:
                print(f"Erro ao ordenar por {self.sort_column}: {e}")
        
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
        """Aplica o filtro atual aos dados - versão corrigida"""
        self.filter_text = self.filter_entry.get().strip()
        
        # Obter dados filtrados e atualizar a tabela
        filtered_data = self.get_filtered_data()
        
        # Limpar widgets existentes exceto cabeçalhos
        for widget in self.scrollable_frame.winfo_children():
            if int(widget.grid_info()['row']) > 0:  # Preservar cabeçalhos (linha 0)
                widget.destroy()
        
        # Ordenar por código para facilitar localização
        sorted_data = filtered_data.sort_values(by='code')
        
        # Mostrar status da filtragem
        print(f"Filtro aplicado: {len(filtered_data)} ações encontradas")
        
        # Processar em lotes para melhor desempenho
        self._populate_table_batch(sorted_data, 0, 50)

    def clear_filter(self):
        """Limpa o filtro atual - versão aprimorada"""
        self.filter_text = ""
        self.filter_entry.delete(0, tk.END)
        self.sector_var.set("Todos")
        self.populate_stock_table()  # Usar populate_stock_table em vez de load_stock_data
    
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
        """Versão otimizada da tabela de ações com rolagem mais suave"""
        # Container para tabela
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
        
        # Adicionar scrollbar horizontal
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=self.canvas.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=x_scrollbar.set)
        
        # Configurar mouse wheel scrolling - mais suave
        self.bind_mousewheel(self.canvas)
        
        # Configura cabeçalhos
        self._setup_table_headers()
        
        # Guardar referência para scroll incrível
        self.populate_stock_table()
        
        # Armazenar atributos para calcular scroll eficiente
        self.last_visible_range = (0, 50)  # Inicializar com valores padrão
        self.all_stock_data = self.performance_data  # Armazenar cópia de todos os dados

    def _on_frame_configure(self, event=None):
        """Configura a região de rolagem corretamente"""
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Ajustar tamanho do canvas se necessário
            width = max(self.scrollable_frame.winfo_reqwidth(), self.canvas.winfo_width())
            height = max(self.scrollable_frame.winfo_reqheight(), self.canvas.winfo_height())
            self.canvas.config(scrollregion=(0, 0, width, height))

    def bind_mousewheel(self, widget):
        """Vincula eventos de rolagem do mouse ao widget com velocidade aumentada"""
        # Bind diretamente ao widget e todos seus filhos
        widget.bind("<MouseWheel>", self._on_mousewheel_faster)  # Windows
        widget.bind("<Button-4>", self._on_mousewheel_faster)  # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel_faster)  # Linux scroll down
        
        # Bind também ao frame principal para garantir que o scroll funcione em toda a área
        self.master.bind("<MouseWheel>", self._on_mousewheel_faster)
        self.master.bind("<Button-4>", self._on_mousewheel_faster)
        self.master.bind("<Button-5>", self._on_mousewheel_faster)

    def _on_mousewheel_faster(self, event):
        """Trata evento de rolagem do mouse com maior velocidade"""
        if not hasattr(self, 'canvas'):
            return
            
        # Velocidade multiplicada por 3 para scroll mais rápido
        if event.num == 4 or event.num == 5:  # Linux
            delta = -3 if event.num == 5 else 3
        else:  # Windows
            delta = int(event.delta/40) * 3  # Aumentar velocidade
        
        self.canvas.yview_scroll(-delta, "units")
        return "break"  # Impedir propagação do evento

    def _check_scroll_end(self, event=None):
        """Verifica se o usuário chegou próximo ao final do scroll para carregar mais dados"""
        if not hasattr(self, 'canvas'):
            return
            
        # Se estiver próximo ao final, carregar mais dados
        bottom = self.canvas.yview()[1]
        if bottom > 0.9:  # Se estiver nos últimos 10% do scroll
            current_visible = self.last_visible_range[1]
            # Carregar mais 50 linhas
            new_end = min(current_visible + 50, len(self.all_stock_data))
            if new_end > current_visible:
                self.populate_visible_rows(current_visible, new_end)

    def populate_stock_table(self):
        """Preenche a tabela com todas as ações - versão corrigida e otimizada"""
        # Limpar widgets existentes exceto cabeçalhos
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info'):
                if int(widget.grid_info().get('row', 0)) > 0:  # Preservar cabeçalhos (linha 0)
                    widget.destroy()
        
        # Obter dados filtrados (usando o método corrigido)
        filtered_data = self.get_filtered_data()
        
        # Verificar se há dados
        if filtered_data.empty:
            ttk.Label(self.scrollable_frame, text="Nenhum dado disponível", font=("Arial", 12)).grid(
                row=1, column=0, padx=10, pady=10, columnspan=13)
            return
        
        print(f"Total de ações após filtros: {len(filtered_data)}")
        
        # Ordenar por código para facilitar localização
        sorted_data = filtered_data.sort_values(by='code')
        
        # Processar em lotes para melhor desempenho
        self._populate_table_batch(sorted_data, 0, 50)

    def _populate_table_batch(self, data, start_idx, batch_size):
        """Versão corrigida que preenche a tabela em lotes"""
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        
        for i, (_, row) in enumerate(batch.iterrows(), start_idx + 1):
            try:
                # Obter dados básicos
                ticker = str(row['code']) if 'code' in row else "N/A"
                
                # Obter valores com segurança usando o método safe_get_value
                price = self.safe_get_value(row, 'current_price')
                open_price = self.safe_get_value(row, 'open_price')
                low_price = self.safe_get_value(row, 'low_price')
                high_price = self.safe_get_value(row, 'high_price') 
                close_price = self.safe_get_value(row, 'close_price')
                
                financial_volume = self.safe_get_value(row, 'volume')
                trades_volume = self.safe_get_value(row, 'trades') if 'trades' in row else 0.0
                
                # Retornos
                daily_change = self.safe_get_value(row, 'daily_return')
                monthly_change = self.safe_get_value(row, 'monthly_return')
                quarterly_change = self.safe_get_value(row, 'quarterly_return')
                yearly_change = self.safe_get_value(row, 'yearly_return')
                ytd_change = self.safe_get_value(row, 'ytd_return')
                
                # Debug - imprimir valores para diagnosticar problemas
                if i % 10 == 0:  # Imprimir a cada 10 linhas para não sobrecarregar
                    print(f"Adicionando ação: {ticker}, preço: {price:.2f}, setor: {row.get('sector', 'N/A')}")
                
                # Adicionar cada célula à tabela com garantia contra erros
                ttk.Label(self.scrollable_frame, text=ticker).grid(row=i, column=0, padx=10, pady=2, sticky="w")
                ttk.Label(self.scrollable_frame, text=f"R$ {price:.2f}").grid(row=i, column=1, padx=10, pady=2, sticky="e")
                
                # Adicionar demais campos
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
                import traceback
                traceback.print_exc()
        
        # Se ainda há mais dados para mostrar, agendar o próximo lote
        if end_idx < len(data):
            self.master.after(10, lambda: self._populate_table_batch(data, end_idx, batch_size))
        else:
            # Terminou, adicionar bindings
            self.add_selection_bindings()
            self.scrollable_frame.update_idletasks()
            print("Tabela preenchida com sucesso!")

    def safe_get_value(self, row, column_name):
        """Extrai com segurança um valor numérico de uma linha do DataFrame"""
        try:
            if column_name in row:
                value = row[column_name]
                if isinstance(value, pd.Series):
                    return float(value.iloc(0))
                else:
                    return float(value)
            return 0.0
        except Exception:
            return 0.0

    def add_selection_bindings(self):
        """Adiciona eventos de clique para seleção de ações na tabela - versão melhorada"""
        # Verificar quantas linhas existem no frame scrollable
        total_rows = self.scrollable_frame.grid_size()[1]
        
        # Limpar bindings anteriores para evitar duplicação
        self.click_bindings = []  # Para manter referências
        
        for row in range(1, total_rows):
            # Para a primeira coluna apenas (suficiente para o evento)
            widgets = self.scrollable_frame.grid_slaves(row=row, column=0)
            if widgets:
                widget = widgets[0]
                # Remover bindings anteriores se existirem
                widget.unbind("<Button-1>")
                widget.unbind("<Double-Button-1>")
                
                # Adicionar novos bindings
                widget.bind("<Button-1>", lambda e, r=row: self._handle_single_click(r))
                widget.bind("<Double-Button-1>", lambda e, r=row: self._handle_double_click(r))
                self.click_bindings.append((widget, row))

    def _handle_single_click(self, row):
        """Função dedicada para tratar cliques simples"""
        self.select_stock_row(row)
        # Armazenar a última linha selecionada para uso em outros contextos
        self.last_selected_row = row

    def _handle_double_click(self, row):
        """Função dedicada para tratar duplos cliques de forma mais confiável"""
        # Imediatamente mostrar o indicador de carregamento
        ticker_widget = self.scrollable_frame.grid_slaves(row=row, column=0)
        if not ticker_widget:
            print(f"Widget não encontrado na linha {row}")
            return
            
        ticker = ticker_widget[0].cget('text')
        print(f"Duplo clique na ação {ticker} (linha {row})")
        
        # Destacar a linha
        self.select_stock_row(row)
        
        # Limpar área de gráficos e mostrar carregando
        for widget in self.chart_display.winfo_children():
            widget.destroy()
            
        loading_label = ttk.Label(
            self.chart_display, 
            text=f"Carregando dados de {ticker}...",
            font=("Arial", 14, "bold")
        )
        loading_label.pack(pady=50)
        self.chart_display.update()  # Forçar atualização imediata
        
        # Usar after com prioridade alta (10ms) para garantir execução rápida
        self.master.after(10, lambda: self.process_stock_chart(ticker))

    def process_stock_chart(self, ticker):
        """Função separada para processar o gráfico após duplo clique"""
        try:
            # Verificar se a ação existe
            ticker_exists = False
            for _, row in self.performance_data.iterrows():
                if row['code'] == ticker:
                    ticker_exists = True
                    break
                    
            if not ticker_exists:
                for widget in self.chart_display.winfo_children():
                    widget.destroy()
                    
                ttk.Label(
                    self.chart_display,
                    text=f"Ação {ticker} não encontrada nos dados",
                    font=("Arial", 14, "bold")
                ).pack(pady=20)
                return
                
            # Se existe, mostrar o gráfico
            self.show_stock_performance(ticker)
            
        except Exception as e:
            for widget in self.chart_display.winfo_children():
                widget.destroy()
                
            ttk.Label(
                self.chart_display,
                text=f"Erro ao processar {ticker}",
                font=("Arial", 14, "bold")
            ).pack(pady=20)
            
            ttk.Label(
                self.chart_display,
                text=str(e),
                foreground="red"
            ).pack(pady=10)
            
            print(f"Erro ao processar ação {ticker}: {e}")

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
        """Mostra o gráfico de rentabilidade da ação selecionada com duplo clique - versão melhorada"""
        # Obter o ticker da ação a partir da primeira coluna
        ticker_widget = self.scrollable_frame.grid_slaves(row=row, column=0)
        if not ticker_widget:
            print(f"Não foi encontrado widget na linha {row}, coluna 0")
            return
            
        ticker = ticker_widget[0].cget('text')
        print(f"Ação selecionada: {ticker}")
        
        # Destacar a linha selecionada (resetar destaques primeiro)
        for r in range(1, self.scrollable_frame.grid_size()[1]):
            for c in range(self.scrollable_frame.grid_size()[0]):
                try:
                    widget = self.scrollable_frame.grid_slaves(row=r, column=c)
                    if widget:
                        widget[0].configure(background=self.master.cget('bg'))
                except Exception as e:
                    print(f"Erro ao limpar destaque: {e}")
        
        # Destacar linha da ação atual
        for col in range(self.scrollable_frame.grid_size()[0]):
            try:
                widget = self.scrollable_frame.grid_slaves(row=row, column=col)
                if widget:
                    widget[0].configure(background='#e0e0ff')  # Cor de destaque leve
            except Exception as e:
                print(f"Erro ao destacar célula: {e}")
        
        # Mostrar mensagem de carregamento primeiro
        for widget in self.chart_display.winfo_children():
            widget.destroy()
            
        loading_label = ttk.Label(self.chart_display, 
                                 text=f"Carregando dados de {ticker}...",
                                 font=("Arial", 14, "bold"))
        loading_label.pack(pady=50)
        self.chart_display.update_idletasks()
        
        # Usar after para permitir que a interface atualize antes de processar
        self.master.after(100, lambda: self.show_stock_performance_with_error_handling(ticker, loading_label))

    def show_stock_performance_with_error_handling(self, ticker, loading_label):
        """Wrapper para show_stock_performance com melhor tratamento de erros"""
        try:
            # Verificar se o ticker realmente existe no dataset
            if ticker not in self.performance_data['code'].values:
                loading_label.destroy()
                ttk.Label(self.chart_display, 
                         text=f"Ação {ticker} não encontrada no conjunto de dados",
                         font=("Arial", 14, "bold")).pack(pady=20)
                ttk.Label(self.chart_display, 
                         text="Verifique se os dados foram carregados corretamente.",
                         font=("Arial", 11)).pack(pady=10)
                return
                
            # Remover label de carregamento e mostrar gráfico
            for widget in self.chart_display.winfo_children():
                widget.destroy()
                
            self.show_stock_performance(ticker)
        except Exception as e:
            # Tratamento de erros aprimorado
            for widget in self.chart_display.winfo_children():
                widget.destroy()
                
            ttk.Label(self.chart_display, 
                     text=f"Erro ao processar dados da ação {ticker}",
                     font=("Arial", 14, "bold")).pack(pady=20)
                     
            ttk.Label(self.chart_display, 
                     text=f"Detalhes do erro: {str(e)}",
                     foreground="red").pack(pady=10)
                     
            print(f"Erro ao processar {ticker}: {str(e)}")

    def show_stock_performance(self, ticker):
        """Mostra o gráfico de rentabilidade de uma ação com datas reais de negociação"""
        # Limpar área de gráficos
        for widget in self.chart_display.winfo_children():
            widget.destroy()
        
        # Mostrar mensagem de carregamento
        loading_label = ttk.Label(self.chart_display, 
                                 text=f"Carregando dados de {ticker}...",
                                 font=("Arial", 14, "bold"))
        loading_label.pack(pady=50)
        self.chart_display.update_idletasks()
        
        try:
            # Obter dados da ação
            stock_data = self.performance_data[self.performance_data['code'] == ticker]
            
            if stock_data.empty:
                loading_label.destroy()
                ttk.Label(self.chart_display, 
                         text=f"Não foram encontrados dados para {ticker}",
                         font=("Arial", 12)).pack(pady=50)
                return
            
            # Importações necessárias
            from datetime import datetime, timedelta
            import pandas_market_calendars as mcal
            
            # Obter calendário da B3
            b3 = mcal.get_calendar('B3')
            
            # Data atual
            current_date = datetime.now()
            
            # Encontrar a última data de negociação (dia útil)
            # Verificar os últimos 10 dias até encontrar um dia útil
            last_trading_day = None
            for days_back in range(10):
                check_date = current_date - timedelta(days=days_back)
                schedule = b3.schedule(start_date=check_date.strftime('%Y-%m-%d'), 
                                      end_date=check_date.strftime('%Y-%m-%d'))
                if not schedule.empty:
                    last_trading_day = check_date
                    break
            
            if last_trading_day is None:
                last_trading_day = current_date  # Fallback se não encontrar
            
            # Obter datas de negociação para diferentes períodos
            today_str = last_trading_day.strftime('%Y-%m-%d')
            
            # Cálculo para 1 dia útil atrás
            daily_start = b3.schedule(end_date=today_str, start_date=(last_trading_day - timedelta(days=10)).strftime('%Y-%m-%d'))
            daily_date = datetime.strptime(str(daily_start.index[-2].date()), '%Y-%m-%d') if len(daily_start) >= 2 else last_trading_day - timedelta(days=1)
            
            # Cálculo para 1 semana útil atrás (aproximadamente 5 dias úteis)
            weekly_start = b3.schedule(end_date=today_str, start_date=(last_trading_day - timedelta(days=30)).strftime('%Y-%m-%d'))
            weekly_date = datetime.strptime(str(weekly_start.index[-6].date()), '%Y-%m-%d') if len(weekly_start) >= 6 else last_trading_day - timedelta(days=7)
            
            # Cálculo para 1 mês útil atrás (aproximadamente 22 dias úteis)
            monthly_start = b3.schedule(end_date=today_str, start_date=(last_trading_day - timedelta(days=60)).strftime('%Y-%m-%d'))
            monthly_date = datetime.strptime(str(monthly_start.index[-22].date()), '%Y-%m-%d') if len(monthly_start) >= 22 else last_trading_day - timedelta(days=30)
            
            # Cálculo para 3 meses úteis atrás (aproximadamente 66 dias úteis)
            quarterly_start = b3.schedule(end_date=today_str, start_date=(last_trading_day - timedelta(days=180)).strftime('%Y-%m-%d'))
            quarterly_date = datetime.strptime(str(quarterly_start.index[-66].date()), '%Y-%m-%d') if len(quarterly_start) >= 66 else last_trading_day - timedelta(days=90)
            
            # Cálculo para 1 ano útil atrás (aproximadamente 252 dias úteis)
            yearly_start = b3.schedule(end_date=today_str, start_date=(last_trading_day - timedelta(days=500)).strftime('%Y-%m-%d'))
            yearly_date = datetime.strptime(str(yearly_start.index[-252].date()), '%Y-%m-%d') if len(yearly_start) >= 252 else last_trading_day - timedelta(days=365)
            
            # Cálculo para início do ano atual
            ytd_date = datetime(last_trading_day.year, 1, 1)
            
            # Definir períodos com datas reais de negociação
            periods = {
                'daily_return': {
                    'label': 'Diária',
                    'start_date': daily_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                },
                'weekly_return': {
                    'label': 'Semanal',
                    'start_date': weekly_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                },
                'monthly_return': {
                    'label': 'Mensal',
                    'start_date': monthly_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                },
                'quarterly_return': {
                    'label': 'Trimestral',
                    'start_date': quarterly_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                },
                'yearly_return': {
                    'label': 'Anual',
                    'start_date': yearly_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                },
                'ytd_return': {
                    'label': 'YTD',
                    'start_date': ytd_date.strftime('%d/%m/%Y'),
                    'end_date': last_trading_day.strftime('%d/%m/%Y')
                }
            }
            
            # Remover mensagem de carregamento
            loading_label.destroy()
            
            # O resto do código para exibir o gráfico permanece o mesmo...
            # Apenas mudamos como as datas são calculadas acima
            
            # Mostrar título
            ttk.Label(self.chart_display, 
                     text=f"Rentabilidade da Ação: {ticker} (Dias Úteis)",
                     font=("Arial", 14, "bold")).pack(pady=10)
            
            # Criar figura para o gráfico
            fig = plt.Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Resto do código continua...
            # [O restante da função permanece essencialmente o mesmo]
            
            # Filtrar apenas colunas disponíveis nos dados
            available_returns = [(col, periods[col]['label'], periods[col]) 
                                for col in periods.keys() 
                                if col in stock_data.columns]
            
            # Extrair valores...
            # ...
            
            if not available_returns:
                ttk.Label(self.chart_display, 
                         text=f"Não foram encontrados dados de rentabilidade para {ticker}",
                         font=("Arial", 12)).pack(pady=50)
                return
            
            # Extrair valores e labels com datas
            values = []
            labels = []
            colors = []
            date_ranges = []
            
            for col, label, period in available_returns:
                try:
                    # Corrigir o uso de float em Series
                    value = stock_data[col].iloc[0]
                    if isinstance(value, pd.Series):
                        value = value.iloc[0]
                    value = float(value)
                    
                    values.append(value)
                    
                    # Label com período e datas
                    period_label = f"{label}\n({period['start_date']} a\n{period['end_date']})"
                    labels.append(period_label)
                    
                    date_ranges.append(f"{period['start_date']} a {period['end_date']}")
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
                       f'{values[i]:.2f}%', ha='center', va=va, fontsize=9, fontweight='bold')
            
            # Configurar eixos e títulos
            ax.set_title(f"Rentabilidade de {ticker} por Período", fontsize=14)
            ax.set_ylabel('Rentabilidade (%)', fontsize=12)
            
            # Ajustar tamanho e rotação das labels do eixo x
            plt.setp(ax.get_xticklabels(), fontsize=8, rotation=0)
            
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
            
            # Adicionar legenda explicativa para os períodos
            legend_frame = ttk.LabelFrame(self.chart_display, text="Períodos de Rentabilidade")
            legend_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Criar grid para a legenda
            ttk.Label(legend_frame, text="Diária:", font=("Arial", 9, "bold")).grid(
                row=0, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['daily_return']['start_date']} a {periods['daily_return']['end_date']}").grid(
                row=0, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(legend_frame, text="Semanal:", font=("Arial", 9, "bold")).grid(
                row=0, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['weekly_return']['start_date']} a {periods['weekly_return']['end_date']}").grid(
                row=0, column=3, padx=10, pady=2, sticky="w")
            
            ttk.Label(legend_frame, text="Mensal:", font=("Arial", 9, "bold")).grid(
                row=1, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['monthly_return']['start_date']} a {periods['monthly_return']['end_date']}").grid(
                row=1, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(legend_frame, text="Trimestral:", font=("Arial", 9, "bold")).grid(
                row=1, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['quarterly_return']['start_date']} a {periods['quarterly_return']['end_date']}").grid(
                row=1, column=3, padx=10, pady=2, sticky="w")
            
            ttk.Label(legend_frame, text="Anual:", font=("Arial", 9, "bold")).grid(
                row=2, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['yearly_return']['start_date']} a {periods['yearly_return']['end_date']}").grid(
                row=2, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(legend_frame, text="YTD:", font=("Arial", 9, "bold")).grid(
                row=2, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(legend_frame, text=f"{periods['ytd_return']['start_date']} a {periods['ytd_return']['end_date']}").grid(
                row=2, column=3, padx=10, pady=2, sticky="w")
            
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
            data_ref = last_trading_day.strftime('%d/%m/%Y')
            
            # Grid para informações com data de referência
            ttk.Label(info_frame, text="Data de Referência:", font=("Arial", 9, "bold")).grid(
                row=0, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=data_ref).grid(
                row=0, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text="Preço Atual:", font=("Arial", 9, "bold")).grid(
                row=0, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=f"R$ {price:.2f}").grid(
                row=0, column=3, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text=f"Abertura ({data_ref}):", font=("Arial", 9, "bold")).grid(
                row=1, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=f"R$ {open_price:.2f}").grid(
                row=1, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text=f"Máxima ({data_ref}):", font=("Arial", 9, "bold")).grid(
                row=1, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=f"R$ {high_price:.2f}").grid(
                row=1, column=3, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text=f"Mínima ({data_ref}):", font=("Arial", 9, "bold")).grid(
                row=2, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=f"R$ {low_price:.2f}").grid(
                row=2, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text=f"Fechamento ({data_ref}):", font=("Arial", 9, "bold")).grid(
                row=2, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=f"R$ {close_price:.2f}").grid(
                row=2, column=3, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text="Volume:", font=("Arial", 9, "bold")).grid(
                row=3, column=0, padx=10, pady=2, sticky="w")
            if volume >= 1_000_000:
                vol_text = f"R$ {volume/1_000_000:.2f}M"
            else:
                vol_text = f"R$ {volume/1_000:.2f}K" if volume > 0 else "R$ 0.00"
            ttk.Label(info_frame, text=vol_text).grid(
                row=3, column=1, padx=10, pady=2, sticky="w")
            
            ttk.Label(info_frame, text="Setor:", font=("Arial", 9, "bold")).grid(
                row=3, column=2, padx=10, pady=2, sticky="w")
            ttk.Label(info_frame, text=sector).grid(
                row=3, column=3, padx=10, pady=2, sticky="w")
            
        except Exception as e:
            # Capturar qualquer erro e exibir mensagem amigável
            print(f"Erro ao gerar gráfico para {ticker}: {str(e)}")
            
            for widget in self.chart_display.winfo_children():
                widget.destroy()
                
            ttk.Label(self.chart_display, 
                     text=f"Não foi possível exibir o gráfico para {ticker}",
                     font=("Arial", 12, "bold")).pack(pady=20)
            
            ttk.Label(self.chart_display, 
                     text=f"Erro: {str(e)}",
                     foreground="red").pack(pady=10)

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