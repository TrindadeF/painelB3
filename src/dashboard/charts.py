# Substituir import de investpy por investiny
import investiny as inv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import Canvas, Frame, StringVar, OptionMenu

class StockChart:
    def __init__(self, master):
        self.master = master
        self.selected_stock = StringVar(master)
        self.compared_stock = StringVar(master)
        self.create_widgets()

    def create_widgets(self):
        self.stock_dropdown = OptionMenu(self.master, self.selected_stock, *self.get_stocks(), command=self.update_chart)
        self.stock_dropdown.pack()

        self.compared_stock_dropdown = OptionMenu(self.master, self.compared_stock, *self.get_stocks(), command=self.update_chart)
        self.compared_stock_dropdown.pack()

        self.chart_frame = Frame(self.master)
        self.chart_frame.pack()

        self.canvas = Canvas(self.chart_frame)
        self.canvas.pack()

    def get_stocks(self):
        # This function should return a list of stock tickers from the Brazilian stock market
        return ['PETR3', 'VALE3', 'ITUB4']  # Example tickers

    def update_chart(self, *args):
        stock = self.selected_stock.get()
        compared_stock = self.compared_stock.get()
        self.plot_chart(stock, compared_stock)

    def plot_chart(self, stock, compared_stock):
        self.canvas.delete("all")
        plt.clf()

        # Fetch stock data
        stock_data = inv.get_historical_data(
            symbol=f"{stock}.SA",
            country="brazil",
            from_date=int(datetime(2022, 1, 1).timestamp()),
            to_date=int(datetime(2023, 1, 1).timestamp()),
            interval="1d"
        )
        compared_stock_data = inv.get_historical_data(
            symbol=f"{compared_stock}.SA",
            country="brazil",
            from_date=int(datetime(2022, 1, 1).timestamp()),
            to_date=int(datetime(2023, 1, 1).timestamp()),
            interval="1d"
        )

        stock_df = pd.DataFrame(stock_data['quotes'])
        stock_df['date'] = pd.to_datetime(stock_df['date'], unit='s')
        stock_df.set_index('date', inplace=True)

        compared_stock_df = pd.DataFrame(compared_stock_data['quotes'])
        compared_stock_df['date'] = pd.to_datetime(compared_stock_df['date'], unit='s')
        compared_stock_df.set_index('date', inplace=True)

        plt.plot(stock_df.index, stock_df['close'], label=stock)
        plt.plot(compared_stock_df.index, compared_stock_df['close'], label=compared_stock)

        plt.title('Comparative Stock Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()

        # Draw the chart on the Tkinter canvas
        self.figure = plt.gcf()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

def plot_comparison_chart(stock1, stock2):
    # Criar uma nova figura
    plt.figure(figsize=(10, 6))
    
    try:
        # Buscar dados das ações
        stock_data1 = inv.get_historical_data(
            symbol=f"{stock1}.SA",
            country="brazil",
            from_date=int(datetime(2022, 1, 1).timestamp()),
            to_date=int(datetime(2023, 1, 1).timestamp()),
            interval="1d"
        )
        stock_data2 = inv.get_historical_data(
            symbol=f"{stock2}.SA",
            country="brazil",
            from_date=int(datetime(2022, 1, 1).timestamp()),
            to_date=int(datetime(2023, 1, 1).timestamp()),
            interval="1d"
        )

        stock_df1 = pd.DataFrame(stock_data1['quotes'])
        stock_df1['date'] = pd.to_datetime(stock_df1['date'], unit='s')
        stock_df1.set_index('date', inplace=True)

        stock_df2 = pd.DataFrame(stock_data2['quotes'])
        stock_df2['date'] = pd.to_datetime(stock_df2['date'], unit='s')
        stock_df2.set_index('date', inplace=True)
        
        # Plotar os dados
        plt.plot(stock_df1.index, stock_df1['close'], label=stock1)
        plt.plot(stock_df2.index, stock_df2['close'], label=stock2)
        
        plt.title(f'Comparação: {stock1} vs {stock2}')
        plt.xlabel('Data')
        plt.ylabel('Preço (R$)')
        plt.legend()
        plt.grid(True)
        
        return plt.gcf()  # Retorna a figura atual
    except Exception as e:
        print(f"Erro ao plotar gráfico de comparação: {e}")
        return None

# Modificar a assinatura da função update_chart para aceitar apenas o código da ação

def update_chart(stock, compared_stock=None):

    if compared_stock is None:
        compared_stock = stock
        
    # Criar uma nova figura
    plt.figure(figsize=(10, 6))
    
    try:
        # Buscar dados das ações
        stock_data = inv.get_historical_data(
            symbol=f"{stock}.SA",
            country="brazil",
            from_date=int(datetime(2022, 1, 1).timestamp()),
            to_date=int(datetime(2023, 1, 1).timestamp()),
            interval="1d"
        )

        stock_df = pd.DataFrame(stock_data['quotes'])
        stock_df['date'] = pd.to_datetime(stock_df['date'], unit='s')
        stock_df.set_index('date', inplace=True)
        
        # Plotar os dados da ação principal
        plt.plot(stock_df.index, stock_df['close'], label=stock)
        
        # Se tiver uma ação para comparação e for diferente da principal, plotar também
        if compared_stock != stock:
            compared_stock_data = inv.get_historical_data(
                symbol=f"{compared_stock}.SA",
                country="brazil",
                from_date=int(datetime(2022, 1, 1).timestamp()),
                to_date=int(datetime(2023, 1, 1).timestamp()),
                interval="1d"
            )

            compared_stock_df = pd.DataFrame(compared_stock_data['quotes'])
            compared_stock_df['date'] = pd.to_datetime(compared_stock_df['date'], unit='s')
            compared_stock_df.set_index('date', inplace=True)

            plt.plot(compared_stock_df.index, compared_stock_df['close'], label=compared_stock)

        plt.title(f'Dados da ação: {stock}')
        plt.xlabel('Data')
        plt.ylabel('Preço (R$)')
        plt.legend()
        plt.grid(True)
        
        plt.show()  # Exibir o gráfico
    except Exception as e:
        print(f"Erro ao atualizar gráfico: {e}")

def create_comparison_chart(stock_codes, parent_frame):
    """
    Cria um gráfico comparativo de evolução de preços normalizado (base 100)
    """
    try:
        # Converter códigos para o formato do Yahoo Finance
        yahoo_codes = [code if code.endswith('.SA') else f"{code}.SA" for code in stock_codes]
        
        # Definir período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Buscar dados históricos
        historical_data = yf.download(
            yahoo_codes, 
            start=start_date,
            end=end_date,
            progress=False
        )
        
        if historical_data.empty:
            print("Nenhum dado histórico disponível para as ações selecionadas")
            return None
            
        # Extrair preços de fechamento
        close_prices = historical_data['Close']
        
        # Normalizar preços (base 100)
        normalized_prices = pd.DataFrame()
        
        for stock in close_prices.columns:
            # Verificar se temos dados suficientes
            if len(close_prices[stock].dropna()) > 0:
                first_valid_price = close_prices[stock].dropna().iloc[0]
                if first_valid_price > 0:  # Evitar divisão por zero
                    normalized_prices[stock] = (close_prices[stock] / first_valid_price) * 100
        
        if normalized_prices.empty:
            print("Nenhum dado normalizado disponível")
            return None
            
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plotar dados normalizados
        for stock in normalized_prices.columns:
            # Extrair código sem .SA para legenda
            display_name = stock.replace('.SA', '')
            ax.plot(normalized_prices.index, normalized_prices[stock], label=display_name)
        
        # Personalizar gráfico
        ax.set_title('Evolução de Preço Normalizado (Base 100)')
        ax.set_ylabel('Preço Normalizado')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Configurar formatação de data no eixo x
        date_format = mdates.DateFormatter('%b-%y')
        ax.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()  # Rotacionar datas
        
        # Criar canvas para o Tkinter
        canvas = FigureCanvasTkAgg(fig, parent_frame)
        canvas.draw()
        
        # Adicionar barra de ferramentas
        toolbar = NavigationToolbar2Tk(canvas, parent_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        return canvas
        
    except Exception as e:
        print(f"Erro ao criar gráfico comparativo: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_return_comparison_chart(data, stock_codes, return_column):
    """
    Cria um gráfico de barras comparando os retornos das ações selecionadas
    
    Args:
        data: DataFrame com dados de desempenho
        stock_codes: Lista de códigos de ações para comparar
        return_column: Coluna de retorno para comparar ('daily_return', 'weekly_return', etc)
    """
    try:
        # Verificar se o nome da coluna está correto
        if return_column not in data.columns:
            # Tentar adicionar o sufixo _return se necessário
            if not return_column.endswith('_return'):
                adjusted_column = f"{return_column}_return"
                if adjusted_column in data.columns:
                    return_column = adjusted_column
                else:
                    print(f"Erro: Coluna de retorno '{return_column}' não encontrada.")
                    print(f"Colunas disponíveis: {data.columns.tolist()}")
                    return None
        
        # Filtrar apenas as ações selecionadas
        filtered_data = data[data['code'].isin(stock_codes)].copy()
        
        if filtered_data.empty:
            print("Nenhum dado encontrado para as ações selecionadas")
            return None
        
        # Configurar figura
        plt.figure(figsize=(10, 6))
        
        # Extrair dados para cada código de ação
        codes = []
        returns = []
        
        # Debug: mostrar colunas disponíveis
        print(f"Colunas disponíveis no DataFrame: {filtered_data.columns.tolist()}")
        
        # Extrair dados para cada código de ação
        for code in stock_codes:
            if code in filtered_data['code'].values:
                try:
                    # Obter a linha específica para o código
                    stock_data = filtered_data[filtered_data['code'] == code]
                    
                    # Verificar se a coluna existe
                    if return_column in stock_data.columns:
                        # Extrair o valor escalar do DataFrame
                        return_value = float(stock_data[return_column].iloc[0])
                        
                        codes.append(code)
                        returns.append(return_value)
                    else:
                        print(f"Aviso: Coluna '{return_column}' não encontrada para o código '{code}'")
                        
                except Exception as e:
                    print(f"Erro ao processar código {code}: {e}")
        
        if not codes:
            print("Nenhum dado válido disponível para os códigos selecionados")
            return None
            
        # Definir cores com base no retorno
        colors = ['#4CAF50' if r > 0 else '#F44336' for r in returns]
        
        # Criar gráfico de barras
        plt.bar(codes, returns, color=colors)
        
        # Adicionar valores nas barras
        for i, v in enumerate(returns):
            plt.text(i, v + (0.5 if v > 0 else -1.5), f'{v:.2f}%', 
                     ha='center', fontweight='bold')
        
        # Personalizar gráfico
        title_map = {
            'daily_return': 'Retorno Diário (%)',
            'weekly_return': 'Retorno Semanal (%)',
            'monthly_return': 'Retorno Mensal (%)',
            'yearly_return': 'Retorno Anual (%)',
        }
        
        plt.title(title_map.get(return_column, f'Comparação de {return_column}'))
        plt.ylabel('Retorno (%)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        return plt.gcf()  # Retorna a figura atual
        
    except Exception as e:
        print(f"Erro ao criar gráfico de comparação: {e}")
        import traceback
        traceback.print_exc()
        return None