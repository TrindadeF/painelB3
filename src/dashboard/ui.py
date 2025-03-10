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
        
        # Remover self.filter_text que não será mais usado
        self.sort_column = ""        # Coluna atual de ordenação
        self.sort_ascending = True   # Direção da ordenação
        
        # Criar um estilo personalizado para os cabeçalhos das colunas
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.create_widgets()
        
    def create_widgets(self):
        """Cria todos os widgets do dashboard - versão simplificada sem comparação"""
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
        
        # REMOVER TODO O CÓDIGO DE FILTRO DE TEXTO ANTIGO
        
        # Adicionar o novo filtro de setor
        self.setup_sector_filter(controls_frame)
        
        # Adicionar botão de limpar cache
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
        self.charts_frame = ttk.LabelFrame(right_frame, text="Gráficos de Rentabilidade")
        self.charts_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Inicializar área de gráficos
        self.create_charts_area(self.charts_frame)
    

    def create_charts_area(self, parent):
        """Cria área simples para exibição de gráficos - versão sem comparação"""
        # Texto de instruções
        ttk.Label(parent, 
                 text="Clique em uma ação para ver sua rentabilidade",
                 font=("Arial", 12)).pack(pady=10)
        
        # Frame para exibir gráficos
        self.chart_display = ttk.Frame(parent)
        self.chart_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mensagem inicial
        ttk.Label(self.chart_display, 
                 text="Selecione uma ação na tabela para ver o gráfico de rentabilidade",
                 font=("Arial", 12)).pack(pady=50)
        
        # Adicionar um botão alternativo para exibir gráfico (além do duplo clique)
        view_button_frame = ttk.Frame(parent)
        view_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(view_button_frame, 
                  text="Exibir Gráfico da Ação Selecionada",
                  command=self.show_selected_stock_graph).pack(side=tk.LEFT, padx=5)
        
        # Adicionar informação sobre atalhos
        ttk.Label(view_button_frame, 
                 text="Atalho: Enter = Exibir Gráfico",
                 font=("Arial", 8)).pack(side=tk.RIGHT, padx=10)

        
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
        status_label.grid(row=1, column=0, columnspan=13, padx=10, pady=5)
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
        ).grid(row=1, column=0, columnspan=13, padx=10, pady=5)
        
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
        status_label.grid(row=1, column=0, columnspan=13, padx=10, pady=5)
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
            ).grid(row=1, column=0, columnspan=13, padx=10, pady=10)
            return
        
        # Exibir status de recarregamento
        ttk.Label(
            self.scrollable_frame, 
            text=f"Mostrando todas as {len(all_data)} ações", 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=13, padx=10, pady=5)
        
        # Ordenar e mostrar todos os dados
        sorted_data = all_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 50, offset=1)  # Começar da linha 2 por causa do status
    

    def setup_sector_filter(self, parent_frame):
        """Configura o filtro de setores - versão corrigida e simplificada"""
        # Criar frame para alinhamento
        filter_controls = ttk.Frame(parent_frame)
        filter_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Label para setor
        ttk.Label(filter_controls, text="Setor:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        # Obter valores únicos de setores e garantir formatação consistente
        sectors = []
        
        if 'sector' in self.performance_data.columns:
            # Normalizar valores e remover duplicatas
            sector_values = self.performance_data['sector'].dropna().unique()
            sector_values = [str(s).strip() for s in sector_values if str(s).strip()]
            sectors = ['Todos'] + sorted(set(sector_values))  # Usando set para garantir valores únicos
            print(f"Setores disponíveis: {sectors}")
        else:
            sectors = ['Todos']
            print("Aviso: Coluna 'sector' não encontrada nos dados")
        
        # Criar combobox de setores
        self.sector_var = tk.StringVar(value='Todos')
        self.sector_combobox = ttk.Combobox(
            filter_controls,
            textvariable=self.sector_var,
            values=sectors,
            width=30,
            state="readonly"
        )
        self.sector_combobox.pack(side=tk.LEFT, padx=5)
        
        # Botões de filtro - Usar apenas o botão de mostrar todas
        ttk.Button(filter_controls, 
                  text="Mostrar Todas as Ações", 
                  command=self.show_all_stocks).pack(side=tk.LEFT, padx=5)
        
        # IMPORTANTE: O binding correto
        self.sector_combobox.bind("<<ComboboxSelected>>", self._on_sector_selected)

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
        loading_label.grid(row=1, column=0, columnspan=13, padx=10, pady=5)
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
            ).grid(row=1, column=0, columnspan=13, padx=10, pady=30)
            return
        
        # Mensagem de resultado
        result_text = f"Mostrando {len(filtered_data)} ações do setor '{selected_sector}'"
        if selected_sector == 'Todos':
            result_text = f"Mostrando todas as {len(filtered_data)} ações"
        
        ttk.Label(
            self.scrollable_frame, 
            text=result_text, 
            font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=13, padx=10, pady=5)
        
        # Preencher tabela com dados filtrados
        sorted_data = filtered_data.sort_values(by='code')
        self._populate_table_batch(sorted_data, 1, 100, offset=1)

    def filter_by_specific_sector(self, selected_sector):
        """Filtra os dados pelo setor específico sem depender de self.sector_var"""
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
        ).grid(row=1, column=0, columnspan=13, padx=10, pady=5)
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
        ).grid(row=1, column=0, columnspan=13, padx=10, pady=5)
        
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
        """Versão corrigida que preenche a tabela em lotes com suporte a deslocamento (offset)"""
        end_idx = min(start_idx + batch_size, len(data))
        batch = data.iloc[start_idx:end_idx]
        
        for i, (_, row) in enumerate(batch.iterrows(), start_idx + 1):
            # Calcular a linha real na grid considerando o offset
            grid_row = i + offset
            
            try:
                # Obter dados básicos
                ticker = str(row['code']) if 'code' in row else "N/A"
                
                # Mostrar o setor para diagnóstico
                sector_value = row['sector'] if 'sector' in row else "N/A"
                
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
                
                # Adicionar cada célula à tabela
                ticker_label = ttk.Label(self.scrollable_frame, text=ticker)
                ticker_label.grid(row=grid_row, column=0, padx=10, pady=2, sticky="w")
                
                # Adicionar tooltip com setor
                self.add_tooltip(ticker_label, f"Setor: {sector_value}")
                
                ttk.Label(self.scrollable_frame, text=f"R$ {price:.2f}").grid(
                    row=grid_row, column=1, padx=10, pady=2, sticky="e")
                
                # Adicionar demais campos
                ttk.Label(self.scrollable_frame, text=f"R$ {open_price:.2f}").grid(
                    row=grid_row, column=2, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {low_price:.2f}").grid(
                    row=grid_row, column=3, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {high_price:.2f}").grid(
                    row=grid_row, column=4, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"R$ {close_price:.2f}").grid(
                    row=grid_row, column=5, padx=10, pady=2, sticky="e")
                
                # Formatação para volumes
                vol_text = f"R$ {financial_volume/1_000_000:.2f}M" if financial_volume >= 1_000_000 else \
                         f"R$ {financial_volume/1_000:.2f}K" if financial_volume > 0 else "R$ 0.00"
                
                ttk.Label(self.scrollable_frame, text=vol_text).grid(
                    row=grid_row, column=6, padx=10, pady=2, sticky="e")
                ttk.Label(self.scrollable_frame, text=f"{trades_volume:,.0f}").grid(
                    row=grid_row, column=7, padx=10, pady=2, sticky="e")
                
                # Formatar as variações com cores
                self.create_change_label(self.scrollable_frame, daily_change, row=grid_row, column=8)
                self.create_change_label(self.scrollable_frame, monthly_change, row=grid_row, column=9)
                self.create_change_label(self.scrollable_frame, quarterly_change, row=grid_row, column=10)
                self.create_change_label(self.scrollable_frame, yearly_change, row=grid_row, column=11)
                self.create_change_label(self.scrollable_frame, ytd_change, row=grid_row, column=12)
                
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
                if isinstance(value, pd.Series):
                    return float(value.iloc(0))
                else:
                    return float(value)
            return 0.0
        except Exception:
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
        """Configura os cabeçalhos da tabela de ações com informações do período"""
        headers = [
            "Ação", "Preço", "Abertura", "Mínima", "Máxima", "Fechamento", 
            "Vol. Financeiro", "Vol. Negócios", "Diário %", "Mensal %", 
            "Trimestral %", "Anual %", "YTD %"
        ]
        
        for col, header in enumerate(headers):
            header_label = ttk.Label(
                self.scrollable_frame, 
                text=header, 
                font=("Arial", 10, "bold")
            )
            header_label.grid(row=0, column=col, padx=10, pady=5)
            
            # Adicionar tooltips explicativos para ajudar o usuário
            if header == "Diário %":
                self.add_tooltip(header_label, "Variação percentual no último dia útil")
            elif header == "Mensal %":
                self.add_tooltip(header_label, "Variação percentual no último mês")
            elif header == "Trimestral %":
                self.add_tooltip(header_label, "Variação percentual nos últimos 3 meses")
            elif header == "Anual %":
                self.add_tooltip(header_label, "Variação percentual nos últimos 12 meses")
            elif header == "YTD %":
                self.add_tooltip(header_label, "Variação percentual desde o início do ano")

    def show_selected_stock_graph(self):
        """Mostra o gráfico da ação atualmente selecionada"""
        if hasattr(self, 'last_selected_row'):
            try:
                ticker_widget = self.scrollable_frame.grid_slaves(row=self.last_selected_row, column=0)
                if ticker_widget:
                    ticker = ticker_widget[0].cget('text')
                    
                    # Mostrar carregando
                    for widget in self.chart_display.winfo_children():
                        widget.destroy()
                        
                    loading_label = ttk.Label(
                        self.chart_display,
                        text=f"Carregando dados de {ticker}...",
                        font=("Arial", 14, "bold")
                    )
                    loading_label.pack(pady=50)
                    self.chart_display.update()
                    
                    # Carregar o gráfico
                    self.master.after(10, lambda: self.process_stock_chart(ticker))
                    return
            except Exception as e:
                print(f"Erro ao mostrar gráfico da ação selecionada: {e}")
        
        # Se não houver seleção, mostrar mensagem
        messagebox.showinfo("Nenhuma Seleção", "Selecione uma ação primeiro clicando nela na tabela.")

    def add_tooltip(self, widget, text):
        """Adiciona tooltip a um widget"""
        def enter(event):
            # Criar janela popup
            x, y, _, _ = widget.bbox("insert")
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
        
        def leave(event):
            self.hide_tooltip()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def hide_tooltip(self):
        """Esconde o tooltip atual se existir"""
        if hasattr(self, 'popup') and self.popup:
            self.popup.destroy()
            self.popup = None