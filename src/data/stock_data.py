import investiny as inv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import time
import random

def get_all_brazil_stocks():
    try:
        stocks = pd.DataFrame(list(get_stock_sectors().keys()), columns=['symbol'])
        return stocks
    except Exception as e:
        print(f"Erro ao obter lista de ações: {e}")
        return pd.DataFrame()

def get_stock_sectors():
    """Retorna um dicionário que mapeia ações aos seus respectivos setores"""
    try:
        sector_mapping = {
            # Financeiro
            'ITUB4.SA': 'Financeiro', 'BBDC4.SA': 'Financeiro', 'B3SA3.SA': 'Financeiro',
            'BBAS3.SA': 'Financeiro', 'SANB11.SA': 'Financeiro',
            
            # Energia/Petróleo
            'PETR3.SA': 'Energia', 'PETR4.SA': 'Energia', 'CSAN3.SA': 'Energia',
            'UGPA3.SA': 'Energia', 'BRDT3.SA': 'Energia',
            
            # Mineração
            'VALE3.SA': 'Mineração', 'CSNA3.SA': 'Mineração', 'GGBR4.SA': 'Mineração',
            'USIM5.SA': 'Mineração',
            
            # Consumo
            'ABEV3.SA': 'Consumo', 'LREN3.SA': 'Consumo', 'MGLU3.SA': 'Consumo',
            'NTCO3.SA': 'Consumo', 'BTOW3.SA': 'Consumo', 'LAME4.SA': 'Consumo',
            
            # Utilities
            'SBSP3.SA': 'Utilities', 'CMIG4.SA': 'Utilities', 'ELET3.SA': 'Utilities',
            'ELET6.SA': 'Utilities', 'CPFE3.SA': 'Utilities',
            
            # Imobiliário
            'BRCR11.SA': 'Imobiliário', 'KNRI11.SA': 'Imobiliário', 'HGLG11.SA': 'Imobiliário',
            
            # Telecomunicações
            'VIVT4.SA': 'Telecomunicações', 'TIMS3.SA': 'Telecomunicações', 'OIBR3.SA': 'Telecomunicações'
        }
        return sector_mapping
    except Exception as e:
        print(f"Erro ao mapear setores: {e}")
        return {}

def fetch_stock_data(stock_code, max_retries=3):
    """Obtém dados históricos de uma ação específica com mecanismo de retry"""
    retries = 0
    
    if not stock_code.endswith('.SA'):
        stock_code = f"{stock_code}.SA"
    
    while retries < max_retries:
        try:
            time.sleep(1 + random.random())
            
            end_date = int(datetime.now().timestamp())
            start_date = int((datetime.now() - timedelta(days=365)).timestamp())
            
            stock_data = inv.get_historical_data(
                symbol=stock_code,
                country="brazil",
                from_date=start_date,
                to_date=end_date,
                interval="1d"
            )
            
            if stock_data and 'quotes' in stock_data:
                df = pd.DataFrame(stock_data['quotes'])
                
                # Converter timestamp para datetime
                df['date'] = pd.to_datetime(df['date'], unit='s')
                df.set_index('date', inplace=True)
                
                # Renomear colunas para manter compatibilidade
                df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)
                
                return df
            else:
                raise Exception(f"Dados não disponíveis para {stock_code}")
                
        except Exception as e:
            retries += 1
            delay = 2 ** retries  # Backoff exponencial
            print(f"Tentativa {retries} falhou para {stock_code}: {e}. Aguardando {delay}s...")
            time.sleep(delay)
    
    print(f"Erro ao obter dados da ação {stock_code} após {max_retries} tentativas.")
    return None

def calculate_returns(stock_data):
    """Calcula retornos diários, semanais, mensais e anuais para uma ação"""
    if stock_data is None or len(stock_data) < 20:  # Pelo menos 20 dias de dados
        return {
            'daily': 0,
            'weekly': 0,
            'monthly': 0,
            'yearly': 0
        }
    
    try:
        # Calcular retornos
        stock_data['daily_return'] = stock_data['Close'].pct_change()
        
        # Retorno diário (último dia)
        daily_return = stock_data['daily_return'].iloc[-1] * 100 if len(stock_data) > 1 else 0
        
        # Retorno semanal (últimos 5 dias úteis ou menos se não houver dados suficientes)
        week_idx = min(6, len(stock_data))
        weekly_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-week_idx]) - 1) * 100 if len(stock_data) > 5 else 0
        
        # Retorno mensal (últimos 21 dias úteis ou menos se não houver dados suficientes)
        month_idx = min(22, len(stock_data))
        monthly_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-month_idx]) - 1) * 100 if len(stock_data) > 21 else 0
        
        # Retorno anual ou máximo período disponível
        yearly_return = ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100
        
        return {
            'daily': daily_return,
            'weekly': weekly_return,
            'monthly': monthly_return,
            'yearly': yearly_return
        }
    except Exception as e:
        print(f"Erro ao calcular retornos: {e}")
        return {
            'daily': 0,
            'weekly': 0,
            'monthly': 0,
            'yearly': 0
        }

def get_stock_performance_data():
    """Obtém dados de desempenho para as principais ações da B3"""
    sectors = get_stock_sectors()
    
    performance_data = []
    
    # Obter apenas 10 ações para reduzir a carga na API
    stock_codes_with_sectors = list(sectors.keys())[:10]
    
    print(f"Buscando dados para {len(stock_codes_with_sectors)} ações...")
    
    for stock_code in stock_codes_with_sectors:
        try:
            # Remover o sufixo .SA para exibição no dashboard
            display_code = stock_code.replace('.SA', '')
            
            stock_data = fetch_stock_data(stock_code)
            if stock_data is not None and not stock_data.empty:
                returns = calculate_returns(stock_data)
                
                # Adicionar ao dataframe de resultados
                sector = sectors.get(stock_code, 'Outros')
                performance_data.append({
                    'code': display_code,  # Exibe código sem .SA
                    'sector': sector,
                    'current_price': stock_data['Close'].iloc[-1],
                    'daily_return': returns['daily'],
                    'weekly_return': returns['weekly'],
                    'monthly_return': returns['monthly'],
                    'yearly_return': returns['yearly']
                })
                print(f"Dados processados com sucesso para {stock_code}")
        except Exception as e:
            print(f"Erro processando ação {stock_code}: {e}")
    
    return pd.DataFrame(performance_data)