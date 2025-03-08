# Substituir import de investpy por investiny
import investiny as inv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta

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

import yfinance as yf
import numpy as np

def create_comparison_chart(selected_stocks, master=None):
    """
    Cria um gráfico comparativo entre as ações selecionadas
    
    Args:
        selected_stocks: Lista de códigos de ações para comparar
        master: Widget Tkinter onde o gráfico será exibido
        
    Returns:
        FigureCanvasTkAgg: Canvas do matplotlib se master é fornecido
        matplotlib figure: Figura do matplotlib caso contrário
    """
    if not selected_stocks:
        return None
        
    plt.figure(figsize=(10, 6))
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Preparar códigos de ticker com .SA
    tickers = []
    for stock in selected_stocks:
        if not stock.endswith('.SA'):
            tickers.append(f"{stock}.SA")
        else:
            tickers.append(stock)
            
    # Baixar dados de todas as ações de uma vez
    try:
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
        
        # Se há apenas uma ação, o formato é diferente
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data['Close']
        else:
            # Para uma única ação
            close_prices = pd.DataFrame(data['Close'])
            close_prices.columns = [tickers[0]]
        
        # Normalizar os dados
        normalized_data = close_prices.copy()
        
        for ticker in normalized_data.columns:
            # Normalizar para começar de 100
            normalized_data[ticker] = 100 * normalized_data[ticker] / normalized_data[ticker].iloc[0]
            plt.plot(normalized_data.index, normalized_data[ticker], label=ticker.replace('.SA', ''))
            
        plt.title("Comparação de Desempenho (Base 100)")
        plt.xlabel("Data")
        plt.ylabel("Preço Normalizado")
        plt.legend()
        plt.grid(True)
        
        if master:
            canvas = FigureCanvasTkAgg(plt.gcf(), master=master)
            canvas.draw()
            return canvas
        else:
            return plt.gcf()
            
    except Exception as e:
        print(f"Erro ao criar gráfico de comparação: {e}")
        return None

def create_return_comparison_chart(performance_df, selected_stocks, return_type='yearly'):
    """
    Cria um gráfico de barras para comparar retornos específicos entre ações
    
    Args:
        performance_df: DataFrame com dados de desempenho
        selected_stocks: Lista de ações para comparar
        return_type: Tipo de retorno ('daily', 'weekly', 'monthly', 'yearly')
    """
    if len(selected_stocks) == 0:
        return None
        
    # Filtrar dados para as ações selecionadas
    filtered_data = performance_df[performance_df['code'].isin([s.replace('.SA', '') for s in selected_stocks])]
    
    if filtered_data.empty:
        return None
        
    # Criar gráfico de barras
    plt.figure(figsize=(10, 6))
    
    return_column = f"{return_type}_return"
    
    # Plotar gráfico de barras
    bars = plt.bar(filtered_data['code'], filtered_data[return_column], color='skyblue')
    
    # Adicionar valor em cada barra
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%', ha='center', va='bottom')
    
    plt.title(f'Comparação de Retorno {return_type.capitalize()}')
    plt.ylabel('Retorno (%)')
    plt.xlabel('Ação')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    return plt.gcf()