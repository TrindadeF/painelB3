import investiny as inv
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
    if not stock_code.endswith('.SA'):
        stock_code = f"{stock_code}.SA"
        
    # Definir datas
    end_date = int(datetime.now().timestamp())
    start_date = int((datetime.now() - timedelta(days=365)).timestamp())
    
    try:
        # Adicionar um pequeno delay para evitar bloqueios
        time.sleep(1 + random.random())
        
        # Obter dados históricos
        stock_data = inv.get_historical_data(
            symbol=stock_code,
            country="brazil",
            from_date=start_date,
            to_date=end_date,
            interval="1d"
        )
        
        if not stock_data or 'quotes' not in stock_data:
            return {
                'year': 0,
                'last_12_months': 0,
                'month': 0,
                'week': 0,
                'day': 0
            }
            
        # Converter para DataFrame
        df = pd.DataFrame(stock_data['quotes'])
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        
        # Calcular desempenho
        performance = {
            'year': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) if len(df) > 252 else 0,
            'last_12_months': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) if len(df) > 252 else 0,
            'month': ((df['close'].iloc[-1] / df['close'].iloc[-22]) - 1) if len(df) > 22 else 0,
            'week': ((df['close'].iloc[-1] / df['close'].iloc[-6]) - 1) if len(df) > 6 else 0,
            'day': (df['close'].pct_change().iloc[-1]) if len(df) > 1 else 0,
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
    end_date = int(datetime.now().timestamp())
    start_date = int((datetime.now() - timedelta(days=365)).timestamp())
    
    try:
        # Obter dados para primeira ação
        time.sleep(1 + random.random())  # Delay para evitar bloqueios
        stock_data1 = inv.get_historical_data(
            symbol=stock_code1,
            country="brazil",
            from_date=start_date,
            to_date=end_date,
            interval="1d"
        )
        
        # Obter dados para segunda ação
        time.sleep(1 + random.random())
        stock_data2 = inv.get_historical_data(
            symbol=stock_code2,
            country="brazil",
            from_date=start_date,
            to_date=end_date,
            interval="1d"
        )
        
        # Verificar se os dados foram obtidos corretamente
        if not stock_data1 or not stock_data2 or 'quotes' not in stock_data1 or 'quotes' not in stock_data2:
            return pd.DataFrame()
            
        # Processar dados
        df1 = pd.DataFrame(stock_data1['quotes'])
        df1['date'] = pd.to_datetime(df1['date'], unit='s')
        df1.set_index('date', inplace=True)
        
        df2 = pd.DataFrame(stock_data2['quotes'])
        df2['date'] = pd.to_datetime(df2['date'], unit='s')
        df2.set_index('date', inplace=True)
        
        # Criar DataFrame de comparação
        comparison_data = pd.DataFrame({
            stock_code1.replace('.SA', ''): df1['close'],
            stock_code2.replace('.SA', ''): df2['close']
        }, index=df1.index)
        
        return comparison_data
    except Exception as e:
        print(f"Erro ao comparar {stock_code1} e {stock_code2}: {e}")
        return pd.DataFrame()