import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import random

def get_market_sectors():
    # Mapeamento manual de setores
    sector_mapping = {
        'Financeiro': ['ITUB4.SA', 'BBDC4.SA', 'B3SA3.SA', 'BBAS3.SA', 'SANB11.SA'],
        'Energia': ['PETR3.SA', 'PETR4.SA', 'CSAN3.SA', 'UGPA3.SA', 'BRDT3.SA'],
        'Mineração': ['VALE3.SA', 'CSNA3.SA', 'GGBR4.SA', 'USIM5.SA'],
        'Consumo': ['ABEV3.SA', 'LREN3.SA', 'MGLU3.SA', 'NTCO3.SA', 'BTOW3.SA', 'LAME4.SA'],
        'Utilities': ['SBSP3.SA', 'CMIG4.SA', 'ELET3.SA', 'ELET6.SA', 'CPFE3.SA'],
        'Imobiliário': ['BRCR11.SA', 'KNRI11.SA', 'HGLG11.SA'],
        'Telecomunicações': ['VIVT4.SA', 'TIMS3.SA', 'OIBR3.SA']
    }
    
    # Criar DataFrames para cada setor
    sector_dict = {}
    for sector, stocks in sector_mapping.items():
        # Criar DataFrame simples com símbolos
        stock_data = [{'symbol': stock, 'name': stock.replace('.SA', '')} for stock in stocks]
        sector_dict[sector] = pd.DataFrame(stock_data)
    
    return sector_dict

def get_stock_performance(stock_code):
    """
    Calcula o desempenho de uma ação em diferentes períodos
    
    Args:
        stock_code: Código da ação (com ou sem sufixo .SA)
    """
    # Adicionar .SA se necessário
    if not stock_code.endswith('.SA'):
        stock_code = f"{stock_code}.SA"
        
    # Definir datas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        # Adicionar um pequeno delay para evitar bloqueios
        time.sleep(1 + random.random())
        
        # Obter dados históricos usando yfinance
        df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            return {
                'year': 0,
                'last_12_months': 0,
                'month': 0,
                'week': 0,
                'day': 0
            }
        
        # Calcular desempenho
        performance = {
            'year': ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) if len(df) > 252 else 0,
            'last_12_months': ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) if len(df) > 252 else 0,
            'month': ((df['Close'].iloc[-1] / df['Close'].iloc[-22]) - 1) if len(df) > 22 else 0,
            'week': ((df['Close'].iloc[-1] / df['Close'].iloc[-6]) - 1) if len(df) > 6 else 0,
            'day': (df['Close'].pct_change().iloc[-1]) if len(df) > 1 else 0,
        }
        return performance
    except Exception as e:
        print(f"Erro ao obter desempenho para {stock_code}: {e}")
        return {
            'year': 0,
            'last_12_months': 0,
            'month': 0,
            'week': 0,
            'day': 0
        }

def compare_stock_performance(stock_code1, stock_code2):
    """
    Compara o desempenho de duas ações
    """
    # Adicionar .SA se necessário
    if not stock_code1.endswith('.SA'):
        stock_code1 = f"{stock_code1}.SA"
    if not stock_code2.endswith('.SA'):
        stock_code2 = f"{stock_code2}.SA"
    
    # Definir datas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        # Obter dados para ambas as ações usando yfinance
        data = yf.download(
            [stock_code1, stock_code2], 
            start=start_date, 
            end=end_date, 
            progress=False
        )
        
        if data.empty:
            return pd.DataFrame()
        
        # Se há apenas uma ação, o formato é diferente
        if isinstance(data.columns, pd.MultiIndex):
            # Organizar dados em formato de comparação
            close_prices = data['Close']
            comparison_data = pd.DataFrame({
                stock_code1.replace('.SA', ''): close_prices[stock_code1],
                stock_code2.replace('.SA', ''): close_prices[stock_code2]
            })
        else:
            # Se tivermos apenas uma ação válida
            comparison_data = pd.DataFrame({
                stock_code1.replace('.SA', ''): data['Close']
            })
        
        return comparison_data
    except Exception as e:
        print(f"Erro ao comparar {stock_code1} e {stock_code2}: {e}")
        return pd.DataFrame()