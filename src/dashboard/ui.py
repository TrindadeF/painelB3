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
        
        # Inicializar variáveis de ordenação
        self.sort_column = "code"    # Inicialmente ordenar por código da ação
        self.sort_ascending = True   # Ordem crescente por padrão
        
        # Criar um estilo personalizado para os cabeçalhos das colunas
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.create_widgets()
        
        # Diagnóstico de dados
        self.verify_duplicate_data()
        
    def create_widgets(self):
        """Cria todos os widgets do dashboard - versão simplificada sem painel de gráficos"""
        # Frame principal 
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame para filtros e controles
        controls_frame = ttk.LabelFrame(main_frame, text="Filtros e Controles")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Título principal
        ttk.Label(controls_frame, text="Dashboard de Ações da B3", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Adicionar o filtro de setor
        self.setup_sector_filter(controls_frame)
        
        # Adicionar botão de limpar cache
        cache_frame = ttk.Frame(controls_frame)
        cache_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(cache_frame, text="Forçar Atualização de Dados", 
                  command=self.clear_data_cache).pack(side=tk.LEFT, padx=5)
        
        # Frame para tabela de ações
        self.stocks_frame = ttk.LabelFrame(main_frame, text="Ações")
        self.stocks_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup da tabela de ações com rolagem
        self.setup_scrollable_stock_table()

        
    def get_filtered_data(self):
        """Retorna os dados filtrados apenas por setor - versão completamente reescrita"""
        data = self.performance_data.copy()
        
        # Verificar se há dados
        if data.empty:
            print("Aviso: Conjunto de dados vazio")
            return data
        
        # Registrar o total de linhas antes da filtragem
        total_rows = len(data)
        print(f"Total de linhas antes do filtro de setor: {total_rows}")
        
        # Aplicar filtro de setor se não for "Todos"
        if hasattr(self, 'sector_var') and self.sector_var.get() != 'Todos':
            selected_sector = self.sector_var.get()
            print(f"Filtrando pelo setor: '{selected_sector}'")
            
            # Verificar se a coluna sector existe
            if 'sector' not in data.columns:
                print("Erro: coluna 'sector' não encontrada nos dados")
                return data
            
            # DEBUG: Mostrar alguns setores da base para comparação
            sample_sectors = data['sector'].dropna().unique()[:5]
            print(f"Amostra de setores na base: {sample_sectors}")
            
            # Normalizar valores para comparação - crucial para correspondência exata
            data['normalized_sector'] = data['sector'].fillna('').astype(str).str.strip()
            normalized_selected = selected_sector.strip()
            
            # Aplicar filtro com correspondência exata
            filtered_data = data[data['normalized_sector'] == normalized_selected].copy()
            
            # Se não encontrar resultados, tentar correspondência parcial
            if filtered_data.empty:
                print(f"Nenhum resultado com correspondência exata para '{selected_sector}'")
                # Tentar correspondência parcial (contains)
                filtered_data = data[data['normalized_sector'].str.contains(normalized_selected, case=False, na=False)].copy()
            
            # Remover coluna temporária 
            if 'normalized_sector' in filtered_data.columns:
                filtered_data.drop('normalized_sector', axis=1, inplace=True)
            
            if 'normalized_sector' in data.columns:
                data.drop('normalized_sector', axis=1, inplace=True)
            
            # Resultado final
            num_filtered = len(filtered_data)
            print(f"Filtro aplicado: {num_filtered} de {total_rows} ações no setor '{selected_sector}'")
            
            # Se não encontrou nada, mostrar alerta
            if num_filtered == 0:
                print(f"ALERTA: Nenhuma ação encontrada para o setor '{selected_sector}'")
                print(f"Setores disponíveis: {data['sector'].dropna().unique()}")
            
            return filtered_data
        
        # Se não há filtro, retornar todos os dados
        return data
    
    def apply_filter(self):
        """Aplica os filtros atuais e atualiza a interface - versão revisada"""
        # Atualizar status antes de aplicar o filtro
        status_label = ttk.Label(
            self.scrollable_frame, 
            text="Aplicando filtros...", 
            font=("Arial", 10, "italic")
        )
        status_label.grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        self.scrollable_frame.update_idletasks()
        
        # Obter texto do filtro
        self.filter_text = self.filter_entry.get().strip()
        selected_sector = self.sector_var.get()
        
        print(f"Aplicando filtros - Texto: '{self.filter_text}', Setor: '{selected_sector}'")
        
        # Limpar widgets existentes exceto cabeçalhos
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:  # Preservar cabeçalhos (linha 0)
                    widget.destroy()
        
        # Obter dados filtrados
        filtered_data = self.get_filtered_data()
        
        # Atualizar interface com resultado da filtragem
        if filtered_data.empty:
            ttk.Label(
                self.scrollable_frame, 
                text=f"Nenhum resultado para: Texto='{self.filter_text}', Setor='{selected_sector}'", 
                font=("Arial", 12)
            ).grid(row=1, column=0, columnspan=13, padx=10, pady=30)
            return
        
        # Mostrar resultados da filtragem
        result_text = f"Encontrado(s) {len(filtered_data)} resultado(s)"
        if self.filter_text:
            result_text += f" para '{self.filter_text}'"
        if selected_sector != 'Todos':
            result_text += f" no setor '{selected_sector}'"
            
        ttk.Label(
            self.scrollable_frame, 
            text=result_text, 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        
        # Ordenar e mostrar dados filtrados
        sorted_data = filtered_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 50, offset=1)  # Começar da linha 2 por causa do status

    def clear_filter(self):
        """Limpa todos os filtros e restaura a visualização original - versão revisada"""
        # Redefinir variáveis de filtro
        self.filter_text = ""
        self.filter_entry.delete(0, tk.END)
        self.sector_var.set("Todos")
        
        # Mostrar status de limpeza
        status_label = ttk.Label(
            self.scrollable_frame, 
            text="Limpando filtros...", 
            font=("Arial", 10, "italic")
        )
        status_label.grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        self.scrollable_frame.update_idletasks()
        
        # Limpar completamente a tabela (exceto cabeçalhos)
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:  # Preservar cabeçalhos (linha 0)
                    widget.destroy()
        
        # Recarregar todos os dados
        all_data = self.performance_data.copy()
        
        # Verificar se há dados
        if all_data.empty:
            ttk.Label(
                self.scrollable_frame, 
                text="Nenhum dado disponível", 
                font=("Arial", 12)
            ).grid(row=1, column=0, columnspan=14, padx=10, pady=10)
            return
        
        # Exibir status de recarregamento
        ttk.Label(
            self.scrollable_frame, 
            text=f"Mostrando todas as {len(all_data)} ações", 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        
        # Ordenar e mostrar todos os dados
        sorted_data = all_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 50, offset=1)  # Começar da linha 2 por causa do status
    

    def setup_sector_filter(self, parent_frame):
        """Configura o filtro de setores e seletor de período para barras visuais"""
        # Criar frame para alinhamento
        filter_controls = ttk.Frame(parent_frame)
        filter_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Label e combobox para setor
        ttk.Label(filter_controls, text="Setor:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        # Obter valores únicos de setores
        sectors = []
        if 'sector' in self.performance_data.columns:
            sector_values = self.performance_data['sector'].dropna().unique()
            sector_values = [str(s).strip() for s in sector_values if str(s).strip()]
            sectors = ['Todos'] + sorted(set(sector_values))
        else:
            sectors = ['Todos']
        
        # Combobox de setores
        self.sector_var = tk.StringVar(value='Todos')
        self.sector_combobox = ttk.Combobox(
            filter_controls,
            textvariable=self.sector_var,
            values=sectors,
            width=20,
            state="readonly"
        )
        self.sector_combobox.pack(side=tk.LEFT, padx=5)
        
        # Botão de mostrar todas
        ttk.Button(filter_controls, 
                  text="Mostrar Todas as Ações", 
                  command=self.show_all_stocks).pack(side=tk.LEFT, padx=5)
        
        # NOVO: Seletor de período para barras de rentabilidade
        ttk.Label(filter_controls, text="Visualizar barras:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        
        # Coleção de períodos disponíveis
        self.period_column_map = {
            'Diário': 'daily_return',
            'Mensal': 'monthly_return',
            'Trimestral': 'quarterly_return', 
            'Anual': 'yearly_return',
            'YTD': 'ytd_return'
        }
        
        # Combobox para seleção de período
        self.visual_period_var = tk.StringVar(value='Mensal')
        self.period_combobox = ttk.Combobox(
            filter_controls,
            textvariable=self.visual_period_var,
            values=list(self.period_column_map.keys()),
            width=12,
            state="readonly"
        )
        self.period_combobox.pack(side=tk.LEFT, padx=5)
        
        # Bindings para eventos
        self.sector_combobox.bind("<<ComboboxSelected>>", self._on_sector_selected)
        self.period_combobox.bind("<<ComboboxSelected>>", self._on_period_selected)
        
        # Inicializar com período mensal
        self.selected_metric = 'monthly_return'

    def _on_sector_selected(self, event=None):
        """Função específica para tratar seleção de setor - versão corrigida"""
        # Obter o valor diretamente do combobox em vez da variável
        selected_sector = self.sector_combobox.get()  # Importante: usar get() diretamente do combobox
        
        print(f"Setor selecionado no combobox: '{selected_sector}'")
        
        # Forçar a atualização explícita da variável
        self.sector_var.set(selected_sector)
        
        # Aplicar filtro após uma pequena pausa para garantir atualização da interface
        self.master.after(50, lambda: self._apply_sector_filter_internal(selected_sector))

    def _apply_sector_filter_internal(self, selected_sector):
        """Método interno para aplicar o filtro com o setor específico"""
        print(f"Aplicando filtro para setor: '{selected_sector}' (interno)")
        
        # Limpar tabela existente
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:
                    widget.destroy()
        
        # Mostrar mensagem de carregamento
        loading_label = ttk.Label(
            self.scrollable_frame, 
            text=f"Filtrando ações do setor: {selected_sector}...", 
            font=("Arial", 10, "italic")
        )
        loading_label.grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        self.scrollable_frame.update()
        
        # Forçar a filtragem específica do setor selecionado
        filtered_data = self.filter_by_specific_sector(selected_sector)
        
        # Limpar tabela novamente
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:
                    widget.destroy()
        
        # Verificar resultado
        if filtered_data.empty:
            ttk.Label(
                self.scrollable_frame, 
                text=f"Nenhuma ação encontrada no setor '{selected_sector}'", 
                font=("Arial", 12)
            ).grid(row=1, column=0, columnspan=14, padx=10, pady=30)
            return
        
        # Mensagem de resultado
        result_text = f"Mostrando {len(filtered_data)} ações do setor '{selected_sector}'"
        if selected_sector == 'Todos':
            result_text = f"Mostrando todas as {len(filtered_data)} ações"
        
        ttk.Label(
            self.scrollable_frame, 
            text=result_text, 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        
        # Preencher tabela com dados filtrados
        if hasattr(self, 'sort_column') and self.sort_column in filtered_data.columns:
            sorted_data = filtered_data.sort_values(
                by=self.sort_column,
                ascending=self.sort_ascending,
                na_position='last'
            )
        else:
            sorted_data = filtered_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 100, offset=1)

        # Atualizar cabeçalhos para refletir ordenação atual
        self._setup_table_headers()

    def filter_by_specific_sector(self, selected_sector):
        """Filtra os dados pelo setor específico preservando ordenação"""
        data = self.performance_data.copy()
        
        # Verificar se há dados
        if data.empty:
            return data
        
        # Se for "Todos", retornar todos os dados
        if selected_sector == 'Todos':
            return data
        
        # Verificar se a coluna sector existe
        if 'sector' not in data.columns:
            print("Erro: coluna 'sector' não encontrada nos dados")
            return data
        
        # DEBUG: Mostrar alguns setores para diagnóstico
        print(f"Filtrando especificamente pelo setor: '{selected_sector}'")
        unique_sectors = data['sector'].dropna().unique()
        print(f"Setores disponíveis ({len(unique_sectors)}): {unique_sectors}")
        
        # Normalizar valores para comparação
        data['normalized_sector'] = data['sector'].fillna('').astype(str).str.strip()
        normalized_selected = selected_sector.strip()
        
        # Verificar cada linha para diagnóstico
        sample_size = min(5, len(data))
        sample_rows = data.sample(sample_size)
        for idx, row in sample_rows.iterrows():
            print(f"Amostra {row['code']}: setor={row['sector']}, normalizado={row['normalized_sector']}")
        
        # Aplicar filtro com correspondência exata
        filtered_data = data[data['normalized_sector'] == normalized_selected].copy()
        
        # Remover coluna temporária
        if 'normalized_sector' in filtered_data.columns:
            filtered_data.drop('normalized_sector', axis=1, inplace=True)
        
        # Limpar original também
        if 'normalized_sector' in data.columns:
            data.drop('normalized_sector', axis=1, inplace=True)
        
        # Resultado final
        print(f"Filtro específico aplicado: {len(filtered_data)} ações encontradas para setor '{selected_sector}'")
        
        # Preservar ordenação atual se definida
        if hasattr(self, 'sort_column') and self.sort_column in filtered_data.columns:
            filtered_data = filtered_data.sort_values(
                by=self.sort_column,
                ascending=self.sort_ascending,
                na_position='last'
            )
        
        return filtered_data

    def show_all_stocks(self):
        """Limpa o filtro de setor e mostra todas as ações"""
        # Redefinir seleção de setor
        self.sector_var.set("Todos")
        
        # Mostrar status
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:
                    widget.destroy()
        
        ttk.Label(
            self.scrollable_frame, 
            text="Carregando todas as ações...", 
            font=("Arial", 10, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        self.scrollable_frame.update()
        
        # Obter todos os dados
        all_data = self.performance_data.copy()
        
        # Limpar tabela novamente
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:
                    widget.destroy()
        
        # Mostrar mensagem de resultado
        ttk.Label(
            self.scrollable_frame, 
            text=f"Mostrando todas as {len(all_data)} ações", 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        
        # Preencher tabela
        sorted_data = all_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 100, offset=1)
        
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

    def _populate_table_batch(self, data, start_idx, batch_size, offset=0):
        """Versão que inclui barras de rentabilidade horizontal"""
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        
        # Determinar qual coluna de rentabilidade está selecionada para visualização
        selected_return_col = self.selected_metric if hasattr(self, 'selected_metric') else 'monthly_return'
        
        for i, (_, row) in enumerate(batch.iterrows(), start_idx + 1):
            # Calcular a linha real na grid considerando o offset
            grid_row = i + offset
            
            try:
                # Obter dados básicos
                ticker = str(row['code']) if 'code' in row else "N/A"
                
                # Executar diagnóstico para ações problemáticas conhecidas
                problematic_tickers = ["ELET6", "ENEV3", "ENGI11", "CMIG4", "CPFE3"]
                if ticker in problematic_tickers:
                    self.debug_value_issues(ticker, row, ["daily_return", "monthly_return", 
                                                        "quarterly_return", "yearly_return"])
                
                # Verificar se os dados estão em branco ou zerados
                visual_value = self.safe_get_value(row, selected_return_col)
                
                # Debug para valores problemáticos
                if pd.isna(visual_value) or visual_value == 0.0:
                    print(f"Atenção: {ticker} tem valor {selected_return_col}={visual_value}")
                
                # Obter valores com segurança
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
                
                # Obter o valor para a barra visual
                visual_value = self.safe_get_value(row, selected_return_col)
                
                # Obter o setor para tooltip
                sector_value = row['sector'] if 'sector' in row else "N/A"
                
                # Adicionar cada célula à tabela
                ticker_label = ttk.Label(self.scrollable_frame, text=ticker)
                ticker_label.grid(row=grid_row, column=0, padx=5, pady=2, sticky="w")
                
                # Adicionar tooltip com setor
                self.add_tooltip(ticker_label, f"Setor: {sector_value}")
                
                # Adicionar demais campos
                ttk.Label(self.scrollable_frame, text=f"R$ {price:.2f}").grid(
                    row=grid_row, column=1, padx=5, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {open_price:.2f}").grid(
                    row=grid_row, column=2, padx=5, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {low_price:.2f}").grid(
                    row=grid_row, column=3, padx=5, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {high_price:.2f}").grid(
                    row=grid_row, column=4, padx=5, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {close_price:.2f}").grid(
                    row=grid_row, column=5, padx=5, pady=2, sticky="e")
                
                # Formatação para volumes
                vol_text = f"R$ {financial_volume/1_000_000:.2f}M" if financial_volume >= 1_000_000 else \
                         f"R$ {financial_volume/1_000:.2f}K" if financial_volume > 0 else "R$ 0.00"
                
                ttk.Label(self.scrollable_frame, text=vol_text).grid(
                    row=grid_row, column=6, padx=5, pady=2, sticky="e")
                
                # Formatação melhorada para quantidade de negócios
                trades_volume = self.safe_get_value(row, 'trades') if 'trades' in row else 0.0

                # Formatação melhorada para quantidade de negócios (mais legível)
                if trades_volume > 1_000_000:
                    trades_text = f"{trades_volume/1_000_000:.2f}M"
                elif trades_volume > 1_000:
                    trades_text = f"{trades_volume/1_000:.1f}K"
                elif trades_volume > 0:
                    trades_text = f"{trades_volume:.0f}"
                else:
                    trades_text = "N/A"

                trades_label = ttk.Label(self.scrollable_frame, text=trades_text)
                trades_label.grid(row=grid_row, column=7, padx=5, pady=2, sticky="e")

                # Adicionar tooltip com informação adicional
                if trades_volume > 0:
                    self.add_tooltip(trades_label, f"Total de {trades_volume:,.0f} negociações")
                
                # Formatar as variações com cores
                self.create_change_label(self.scrollable_frame, daily_change, row=grid_row, column=8)
                self.create_change_label(self.scrollable_frame, monthly_change, row=grid_row, column=9)
                self.create_change_label(self.scrollable_frame, quarterly_change, row=grid_row, column=10)
                self.create_change_label(self.scrollable_frame, yearly_change, row=grid_row, column=11)
                self.create_change_label(self.scrollable_frame, ytd_change, row=grid_row, column=12)
                
                # NOVO: Adicionar barra visual de rentabilidade
                self.create_performance_bar(
                    self.scrollable_frame, visual_value, 
                    max_value=30, row=grid_row, column=13
                )
                
            except Exception as e:
                print(f"Erro ao adicionar ação {i} ({ticker if 'ticker' in locals() else 'desconhecida'}): {e}")
                import traceback
                traceback.print_exc()
        
        # Se ainda há mais dados para mostrar, agendar o próximo lote
        if end_idx < len(data):
            self.master.after(10, lambda: self._populate_table_batch(data, end_idx, batch_size, offset))
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
                
                # Caso 1: Valor é uma Series
                if isinstance(value, pd.Series):
                    if len(value) > 0:
                        try:
                            # Acessar explicitamente o primeiro valor com iloc[0]
                            return float(value.iloc[0])
                        except Exception as e:
                            print(f"Erro ao converter Series para {row.get('code','')}.{column_name}: {str(e)}")
                            # Se o primeiro valor for string, tente converter com tratamento adicional
                            try:
                                first_val = value.iloc[0]
                                if isinstance(first_val, str):
                                    return float(first_val.replace(',', '.'))
                                return 0.0
                            except:
                                return 0.0
                    return 0.0
                
                # Caso 2: Valor é None ou NaN
                elif pd.isna(value):
                    return 0.0
                
                # Caso 3: Valor é um tipo básico (int, float, etc)
                else:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        print(f"Erro ao converter {row.get('code','')}.{column_name}={value} ({type(value)})")
                        return 0.0
                        
            return 0.0
        except Exception as e:
            print(f"Erro ao processar {row.get('code','desconhecido')}.{column_name}: {str(e)}")
            return 0.0

    def add_selection_bindings(self):
        """Adiciona eventos de clique para seleção de ações na tabela - versão simplificada"""
        # Verificar quantas linhas existem no frame scrollable
        total_rows = self.scrollable_frame.grid_size()[1]
        
        # Limpar bindings anteriores para evitar duplicação
        self.click_bindings = []  # Para manter referências
        
        for row in range(1, total_rows):
            # Para a primeira coluna apenas (suficiente para o evento)
            widgets = self.scrollable_frame.grid_slaves(row=row, column=0)
            if widgets:
                widget = widgets[0]
                # Remover bindings anteriores
                widget.unbind("<Button-1>")
                widget.unbind("<Double-Button-1>")
                widget.unbind("<Return>")
                
                # Adicionar novos bindings
                widget.bind("<Button-1>", lambda e, r=row: self._handle_single_click(r))
                widget.bind("<Double-Button-1>", lambda e, r=row: self._handle_double_click(r))
                # Adicionar binding para Enter para facilitar o uso com teclado
                widget.bind("<Return>", lambda e, r=row: self._handle_double_click(r))
                
                self.click_bindings.append((widget, row))
        
        # Adicionar binding global para Enter
        self.master.bind("<Return>", lambda e: self.show_selected_stock_graph())

    def _handle_single_click(self, row):
        """Função dedicada para tratar cliques simples"""
        self.select_stock_row(row)
        # Armazenar a última linha selecionada para uso em outros contextos
        self.last_selected_row = row

    def _handle_double_click(self, row):
        """Função simplificada de duplo clique - apenas destaca a linha"""
        # Destacar a linha
        self.select_stock_row(row)
        
        # Obter ticker para feedback
        ticker_widget = self.scrollable_frame.grid_slaves(row=row, column=0)
        if ticker_widget:
            ticker = ticker_widget[0].cget('text')
            print(f"Linha selecionada: {ticker}")

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
                
                # Definir variável de ambiente para forçar período maior
                import os
                os.environ['FORCE_EXTENDED_DATA'] = 'True'
                
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

    def _setup_table_headers(self):
        """Configura os cabeçalhos da tabela de ações com ordenação interativa"""
        selected_metric = self.selected_metric if hasattr(self, 'selected_metric') else 'monthly_return'
        selected_period = self.visual_period_var.get() if hasattr(self, 'visual_period_var') else "Mensal"
        
        headers = [
            {"name": "Ação", "column": "code", "width": 10},
            {"name": "Preço", "column": "current_price", "width": 10},
            {"name": "Abertura", "column": "open_price", "width": 10},
            {"name": "Mínima", "column": "low_price", "width": 10},
            {"name": "Máxima", "column": "high_price", "width": 10},
            {"name": "Fechamento", "column": "close_price", "width": 13},
            {"name": "Volume R$", "column": "volume", "width": 10},       # Clarificado o nome
            {"name": "Qtd Negócios", "column": "trades", "width": 13},     # Clarificado o nome
            {"name": "Diario %", "column": "daily_return", "width": 10},
            {"name": "Mensal %", "column": "monthly_return", "width": 10},
            {"name": "Trimestral %", "column": "quarterly_return", "width": 13},
            {"name": "Anual %", "column": "yearly_return", "width": 10},
            {"name": "YTD %", "column": "ytd_return", "width": 10},
            {"name": f"Rentabilidade {selected_period}", "column": selected_metric, "width": 20},  
        ]
        
        for col, header in enumerate(headers):
            # Criar um frame para o cabeçalho para poder adicionar indicador de ordenação
            header_frame = ttk.Frame(self.scrollable_frame)
            header_frame.grid(row=0, column=col, padx=9, pady=9, sticky="w")
            
            # Verificar se esta coluna é a de ordenação atual
            sort_indicator = ""
            if hasattr(self, 'sort_column') and self.sort_column == header["column"]:
                sort_indicator = " ▲" if self.sort_ascending else " ▼"
                
            header_label = ttk.Label(
                header_frame, 
                text=f"{header['name']}{sort_indicator}",
                font=("Arial", 10, "bold"),
                width=header.get('width', 10),
                cursor="hand2"  # Todas as colunas agora são clicáveis
            )
            header_label.pack(side=tk.LEFT)
            
            # Vincular evento de clique para ordenação
            header_label.bind("<Button-1>", lambda e, col=header["column"]: self.sort_table_by_column(col))
            
            # Adicionar tooltips explicativos
            tooltip_text = f"Clique para ordenar por {header['name']}"
            if header["name"] == "D %":
                tooltip_text = "Variação percentual no último dia útil (clique para ordenar)"
            elif header["name"] == "M %":
                tooltip_text = "Variação percentual no último mês (clique para ordenar)"
            elif header["name"] == "T %":
                tooltip_text = "Variação percentual nos últimos 3 meses (clique para ordenar)"
            elif header["name"] == "A %":
                tooltip_text = "Variação percentual nos últimos 12 meses (clique para ordenar)"
            elif header["name"] == "YTD %":
                tooltip_text = "Variação percentual desde o início do ano (clique para ordenar)"
            elif "Rentabilidade" in header["name"]:
                tooltip_text = f"Visualização gráfica da rentabilidade {selected_period.lower()} (clique para ordenar)"
                
            self.add_tooltip(header_label, tooltip_text)

    def add_tooltip(self, widget, text):
        """Adiciona tooltip a um widget com tratamento de erros"""
        def enter(event):
            # Criar janela popup com verificação de erros
            try:
                # Verificar se o widget ainda existe e tem bbox
                if not widget.winfo_exists():
                    return
                    
                bbox = widget.bbox("insert")
                if not bbox:  # Se bbox for None, usar coordenadas alternativas
                    x = widget.winfo_rootx() + 20
                    y = widget.winfo_rooty() + 20
                else:
                    x, y, _, _ = bbox
                    x += widget.winfo_rootx() + 25
                    y += widget.winfo_rooty() + 20
                
                # Remover popup existente
                self.hide_tooltip()
                
                # Criar novo popup
                self.popup = tk.Toplevel(widget)
                self.popup.wm_overrideredirect(True)
                self.popup.wm_geometry(f"+{x}+{y}")
                
                label = ttk.Label(self.popup, text=text, background="#ffffe0", 
                                relief="solid", borderwidth=1, font=("Arial", 9))
                label.pack(ipadx=5, ipady=2)
            except Exception as e:
                print(f"Erro ao mostrar tooltip: {e}")
        
        def leave(event):
            self.hide_tooltip()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def hide_tooltip(self):
        """Esconde o tooltip atual se existir"""
        if hasattr(self, 'popup') and self.popup:
            self.popup.destroy()
            self.popup = None

    def sort_table_by_column(self, column):
        """Ordena a tabela por uma coluna específica, alternando entre ascendente e descendente"""
        # Verificar se estamos ordenando pela mesma coluna
        if hasattr(self, 'sort_column') and self.sort_column == column:
            # Inverter a direção de ordenação
            self.sort_ascending = not self.sort_ascending
        else:
            # Nova coluna, definir como ordenação padrão
            self.sort_column = column
            self.sort_ascending = True
        
        print(f"Ordenando por {column}, {'ascendente' if self.sort_ascending else 'descendente'}")
        
        # Aplicar a ordenação e atualizar a tabela
        self.update_table_with_sorted_data()

    def update_table_with_sorted_data(self):
        """Atualiza a tabela com dados ordenados pela coluna selecionada"""
        # Limpar widgets existentes exceto cabeçalhos
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'grid_info') and widget.grid_info():
                if int(widget.grid_info().get('row', 0)) > 0:  # Preservar cabeçalhos
                    widget.destroy()
        
        # Obter dados filtrados atuais
        if hasattr(self, 'sector_var') and self.sector_var.get() != 'Todos':
            filtered_data = self.filter_by_specific_sector(self.sector_var.get())
        else:
            filtered_data = self.performance_data.copy()
        
        # Verificar se temos dados
        if filtered_data.empty:
            ttk.Label(
                self.scrollable_frame, 
                text="Nenhum dado disponível para exibição",
                font=("Arial", 12)
            ).grid(row=1, column=0, columnspan=13, padx=10, pady=30)
            return
        
        # Ordenar dados com base na coluna e direção selecionadas
        if self.sort_column in filtered_data.columns:
            sorted_data = filtered_data.sort_values(
                by=self.sort_column, 
                ascending=self.sort_ascending,
                na_position='last'  # Colocar valores NaN no final
            )
        else:
            # Se a coluna não existir, usar 'code' como fallback
            sorted_data = filtered_data.sort_values(by='code')
            print(f"Aviso: Coluna '{self.sort_column}' não encontrada, ordenando por código")
        
        # Mostrar mensagem de resultados
        selected_sector = self.sector_var.get() if hasattr(self, 'sector_var') else "Todos"
        
        # Obter nome legível para a coluna de ordenação
        column_names = {
            "code": "Ação", 
            "current_price": "Preço", 
            "daily_return": "Rentabilidade diária",
            "monthly_return": "Rentabilidade mensal", 
            "quarterly_return": "Rentabilidade trimestral",
            "yearly_return": "Rentabilidade anual", 
            "ytd_return": "Rentabilidade YTD",
            "trades": "Quantidade de Negócios",  # Adicionado
            "volume": "Volume Financeiro"  # Adicionado
        }
        
        column_display = column_names.get(self.sort_column, self.sort_column)
        
        result_text = f"Mostrando {len(sorted_data)} ações"
        if selected_sector != "Todos":
            result_text += f" do setor '{selected_sector}'"
        
        result_text += f" - Ordenado por {column_display} {'(crescente) ↑' if self.sort_ascending else '(decrescente) ↓'}"
        
        ttk.Label(
            self.scrollable_frame, 
            text=result_text, 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=14, padx=10, pady=5)
        
        # Preencher tabela com dados ordenados
        self._populate_table_batch(sorted_data, 1, 100, offset=1)
        
        # Atualizar os cabeçalhos para mostrar qual coluna está ordenada
        self._setup_table_headers()
        
        # Atualizar cabeçalho da coluna de barras para mostrar o período atual
        self.update_bar_column_header()
    
    def update_bar_column_header(self):
        """Atualiza o cabeçalho da coluna de barras para mostrar o período atual"""
        if not hasattr(self, 'scrollable_frame'):
            return
            
        # Obter o widget do cabeçalho da coluna de barras (última coluna)
        header_widgets = self.scrollable_frame.grid_slaves(row=0, column=13)
        if not header_widgets:
            return
            
        # Procurar pelo label dentro do frame do cabeçalho
        header_frame = header_widgets[0]
        for widget in header_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                # Obter o período atual selecionado
                period = self.visual_period_var.get() if hasattr(self, 'visual_period_var') else "Mensal"
                widget.config(text=f"Rentabilidade {period}")
                
                # Atualizar tooltip
                self.add_tooltip(widget, f"Visualização gráfica da rentabilidade {period.lower()}")
                break

    def create_performance_bar(self, parent, value, max_value=30, row=0, column=0):
        """Cria uma barra horizontal para visualizar a rentabilidade"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, padx=5, pady=2, sticky="w")
        
        # Definir tamanho da barra
        bar_width = 200  # largura total disponível
        
        # Garantir que o valor está dentro dos limites
        if pd.isna(value):
            value = 0
        
        # Limitar valor para visualização
        capped_value = max(min(value, max_value), -max_value)
        
        # Calcular tamanho da barra proporcional ao valor
        bar_size = int(abs(capped_value) / max_value * (bar_width/2))
        
        # Criar canvas para desenhar a barra
        canvas = tk.Canvas(frame, width=bar_width, height=15, bd=0, highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        
        # Desenhar fundo claro para melhor visibilidade
        bg_color = "#f0f0ff" if (hasattr(self, 'sort_column') and 
                               self.sort_column == self.selected_metric) else "#f8f8f8"
        canvas.create_rectangle(0, 0, bar_width, 15, fill=bg_color, outline="")
        
        # Linha central (zero)
        canvas.create_line(bar_width/2, 0, bar_width/2, 15, fill="gray")
        
        # Desenhar a barra
        if value > 0:
            # Barra positiva (à direita)
            canvas.create_rectangle(
                bar_width/2, 3, 
                bar_width/2 + bar_size, 12, 
                fill="#4CAF50", outline="")  # Verde mais suave
        elif value < 0:
            # Barra negativa (à esquerda)
            canvas.create_rectangle(
                bar_width/2 - bar_size, 3, 
                bar_width/2, 12, 
                fill="#F44336", outline="")  # Vermelho mais suave
        
        # Adicionar valor como texto
        text_x = bar_width/2 + 5 if value >= 0 else bar_width/2 - 5
        value_text = f"{value:.1f}%" if not pd.isna(value) else "N/A"
        value_color = "#006400" if value > 0 else "#8B0000" if value < 0 else "black"
        
        # Adicionar o texto diretamente no canvas
        canvas.create_text(
            text_x, 7.5, 
            text=value_text,
            fill=value_color,
            font=("Arial", 8, "bold"),
            anchor="w" if value >= 0 else "e"
        )
        
        # Adicionar tooltip com valor exato
        if not pd.isna(value):
            period = self.visual_period_var.get() if hasattr(self, 'visual_period_var') else "Mensal"
            self.add_tooltip(canvas, f"Rentabilidade {period.lower()}: {value:.2f}%")
        
        return frame

    def _on_period_selected(self, event=None):
        """Atualiza a visualização quando o período é alterado - versão completamente corrigida"""
        # Obter diretamente do combobox para garantir valor atualizado
        selected_period = self.period_combobox.get()
        
        # Imprimir informações de diagnóstico
        print(f"Período selecionado no combobox: '{selected_period}'")
        print(f"Valor atual da variável visual_period_var: '{self.visual_period_var.get()}'")
        
        # Obter coluna correspondente
        new_metric = self.period_column_map.get(selected_period, 'monthly_return')
        old_metric = self.selected_metric if hasattr(self, 'selected_metric') else 'monthly_return'
        
        print(f"Comparando métricas - antiga: '{old_metric}', nova: '{new_metric}'")
        
        # Forçar atualização da variável StringVar
        self.visual_period_var.set(selected_period)
        
        # Atualizar a métrica selecionada independentemente de parecer igual
        self.selected_metric = new_metric
        print(f"Atualizando métrica para: '{new_metric}'")
        
        # Verificar ordenação
        if hasattr(self, 'sort_column') and self.sort_column in self.period_column_map.values():
            print(f"Atualizando coluna de ordenação de '{self.sort_column}' para '{new_metric}'")
            self.sort_column = new_metric
        
        # Desativar eventos temporariamente para evitar loops
        self.period_combobox.unbind("<<ComboboxSelected>>")
        
        # Atualizar a interface
        try:
            self._setup_table_headers()  # Atualizar cabeçalhos
            self.update_bar_column_header()  # Atualizar título da coluna de barras
            self.update_table_with_sorted_data()  # Atualizar tabela
        finally:
            # Restaurar binding após um pequeno delay
            try:
                if self.master.winfo_exists():
                    self.master.after(200, lambda: self.period_combobox.bind("<<ComboboxSelected>>", self._on_period_selected))
            except Exception as e:
                print(f"Erro ao re-associar binding: {e}")

    def verify_duplicate_data(self):
        """Verifica e lista ações que possuem valores idênticos suspeitos"""
        print("\n===== DIAGNÓSTICO DE DADOS =====")
        
        # Dicionário para armazenar valores de retorno por porcentagem
        return_dict = {}
        suspicious_pairs = []
        
        # Colunas a verificar
        check_columns = ['daily_return', 'monthly_return', 'quarterly_return', 'yearly_return', 'ytd_return']
        
        # Para cada linha nos dados
        for _, row in self.performance_data.iterrows():
            ticker = row.get('code', 'UNKNOWN')
            
            # Criar uma tupla com valores arredondados para 1 casa decimal 
            # (para reduzir detecção de falsos duplicados por causa do ruído)
            returns = tuple(round(self.safe_get_value(row, col), 1) for col in check_columns)
            
            # Se encontrar valores idênticos
            if returns in return_dict:
                # Esta ação tem valores idênticos a outra já processada
                matching_ticker = return_dict[returns]
                suspicious_pairs.append((ticker, matching_ticker, returns))
            else:
                # Adiciona esta ação ao dicionário
                return_dict[returns] = ticker
        
        # Exibir resultados
        if suspicious_pairs:
            print(f"ATENÇÃO: Encontrados {len(suspicious_pairs)} pares de ações com dados muito similares!")
            for i, pair in enumerate(suspicious_pairs):
                ticker1, ticker2, values = pair
                if i < 10:  # Limitar a exibição para não sobrecarregar o console
                    print(f"- {ticker1} e {ticker2} têm valores similares: {values}")
            
            if len(suspicious_pairs) > 10:
                print(f"... e mais {len(suspicious_pairs)-10} pares")
                
        else:
            print("Nenhum par de ações com dados exatamente idênticos encontrado.")
        
        # Resumo por tipo de dado
        print("\nResumo da qualidade dos dados:")
        for col in check_columns:
            values = [self.safe_get_value(row, col) for _, row in self.performance_data.iterrows()]
            unique_values = len(set(round(v, 2) for v in values if not pd.isna(v)))
            zeros = sum(1 for v in values if abs(v) < 0.01)
            print(f"- {col}: {unique_values} valores únicos, {zeros} zeros ({zeros/len(values)*100:.1f}%)")

    def _check_raw_data(self, ticker):
        """Verifica dados brutos da fonte para um ticker específico"""
        try:
            from data.stock_data import fetch_stock_data
            print(f"\nVERIFICANDO DADOS BRUTOS para {ticker}:")
            
            # Adicionar .SA se não estiver presente
            full_ticker = f"{ticker}.SA" if not ticker.endswith('.SA') else ticker
            
            # Buscar dados diretamente
            raw_data = fetch_stock_data(full_ticker)
            
            # Correção: Pandas DataFrame tem apenas .empty (não tem is_empty)
            if raw_data is None or raw_data.empty:
                print(f"Não foi possível obter dados brutos para {ticker}")
            else:
                # Mostrar as últimas linhas dos dados
                print(f"Últimos dados para {ticker}:")
                print(raw_data.tail(3))
                
                # Calcular alguns valores básicos para verificar
                if len(raw_data) > 1:
                    last_close = raw_data['Close'].iloc[-1]
                    prev_close = raw_data['Close'].iloc[-2]
                    daily_change = ((last_close/prev_close) - 1) * 100
                    print(f"Variação diária calculada: {daily_change:.2f}%")
        except Exception as e:
            print(f"Erro ao verificar dados brutos para {ticker}: {str(e)}")

def calculate_returns(historical_data):
    """Calcula os retornos para diferentes períodos com verificações adicionais"""
    returns = {
        'daily': 0.0,
        'weekly': 0.0,
        'monthly': 0.0,
        'quarterly': 0.0,
        'yearly': 0.0
    }
    
    try:
        # Verifica se há dados suficientes
        if historical_data.empty or len(historical_data) < 2:
            print("Dados históricos insuficientes para calcular retornos")
            return returns
        
        # Ordena os dados por data para garantir cálculos corretos
        historical_data = historical_data.sort_index()
        
        # Calcula a variação diária (desde o dia anterior)
        if len(historical_data) >= 2:
            latest = historical_data['Close'].iloc[-1]
            previous = historical_data['Close'].iloc[-2]
            returns['daily'] = ((latest / previous) - 1) * 100
            
        # Calcula variações de períodos maiores com verificação de dados suficientes
        periods = {
            'weekly': 5,      # ~5 dias úteis
            'monthly': 21,    # ~21 dias úteis
            'quarterly': 63,  # ~63 dias úteis
            'yearly': 252     # ~252 dias úteis
        }
        
        for period_name, days in periods.items():
            if len(historical_data) > days:
                latest = historical_data['Close'].iloc[-1]
                past = historical_data['Close'].iloc[-min(days, len(historical_data)-1)]
                returns[period_name] = ((latest / past) - 1) * 100
                print(f"Calculado {period_name} para histórico de {len(historical_data)} dias: {returns[period_name]:.2f}%")
            else:
                print(f"Dados insuficientes para {period_name}: {len(historical_data)} < {days}")
        
        return returns
    except Exception as e:
        print(f"Erro ao calcular retornos: {str(e)}")
        return returns