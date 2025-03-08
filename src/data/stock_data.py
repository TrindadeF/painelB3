import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import time
import random
import logging
import requests

# Configurar logging
logging.getLogger('yfinance').setLevel(logging.ERROR)

def get_all_brazil_stocks():
    """
    Obtém lista completa de ações da B3
    Combina uma lista base com outras ações detectadas por setor
    """
    try:
        # Primeiro, obter nossa lista base de setores
        base_stocks = list(get_stock_sectors().keys())
        
        # Segundo, tentar obter mais ações via Yahoo Finance
        # Lista de índices brasileiros para extrair componentes
        indices = ['IBOV', 'IBRX', 'SMLL', 'IDIV', 'MLCX']
        additional_stocks = set()
        
        for index_code in indices:
            try:
                index = yf.Ticker(f"^{index_code}")
                time.sleep(1)  # Evitar rate limiting
                if hasattr(index, 'composition') and index.composition is not None:
                    for stock in index.composition:
                        if stock.endswith('.SA'):
                            additional_stocks.add(stock)
            except Exception as e:
                print(f"Erro ao obter componentes do índice {index_code}: {e}")
                
        # Combinar as duas listas
        all_stocks = list(set(base_stocks).union(additional_stocks))
        
        # Filtrar apenas ações válidas (tentar verificar se existem)
        valid_stocks = []
        batches = [all_stocks[i:i+20] for i in range(0, len(all_stocks), 20)]  # Processar em lotes de 20
        
        for batch in batches:
            try:
                # Verificar rapidamente se as ações existem
                data = yf.download(batch, period='1d', progress=False)
                if isinstance(data, pd.DataFrame) and 'Close' in data.columns:
                    for stock in batch:
                        if stock in data['Close'].columns and not pd.isna(data['Close'][stock].iloc[-1]):
                            valid_stocks.append(stock)
                elif isinstance(data.columns, pd.MultiIndex):
                    valid_in_batch = [stock for stock in batch if stock in data['Close'].columns 
                                      and not data['Close'][stock].empty 
                                      and not pd.isna(data['Close'][stock].iloc[-1])]
                    valid_stocks.extend(valid_in_batch)
            except Exception as e:
                print(f"Erro ao verificar lote de ações: {e}")
            
            time.sleep(1)  # Evitar rate limiting
        
        # Adicionar manualmente as nossas ações principais se elas não foram detectadas
        for stock in base_stocks:
            if stock not in valid_stocks:
                valid_stocks.append(stock)
                
        # Criar DataFrame com as ações válidas
        stocks_df = pd.DataFrame({'symbol': valid_stocks})
        return stocks_df
    except Exception as e:
        print(f"Erro ao obter lista de ações: {e}")
        # Fallback para nossa lista manual
        return pd.DataFrame({'symbol': list(get_stock_sectors().keys())})

def get_stock_sectors():
    """Retorna um dicionário que mapeia ações aos seus respectivos setores"""
    try:
        sector_mapping = {
            # Financeiro
            'ITUB4.SA': 'Financeiro', 'BBDC4.SA': 'Financeiro', 'B3SA3.SA': 'Financeiro',
            'BBAS3.SA': 'Financeiro', 'SANB11.SA': 'Financeiro', 'BBSE3.SA': 'Financeiro',
            'IRBR3.SA': 'Financeiro', 'WEGE3.SA': 'Financeiro',
            
            # Energia/Petróleo
            'PETR3.SA': 'Energia', 'PETR4.SA': 'Energia', 'CSAN3.SA': 'Energia',
            'UGPA3.SA': 'Energia', 'PRIO3.SA': 'Energia', 'RAPT4.SA': 'Energia',
            'VBBR3.SA': 'Energia', 'ENAT3.SA': 'Energia',
            
            # Mineração
            'VALE3.SA': 'Mineração', 'CSNA3.SA': 'Mineração', 'GGBR4.SA': 'Mineração',
            'USIM5.SA': 'Mineração', 'GOAU4.SA': 'Mineração', 'BRAP4.SA': 'Mineração',
            
            # Consumo
            'ABEV3.SA': 'Consumo', 'LREN3.SA': 'Consumo', 'MGLU3.SA': 'Consumo',
            'NTCO3.SA': 'Consumo', 'AMER3.SA': 'Consumo', 'LWSA3.SA': 'Consumo', 
            'CRFB3.SA': 'Consumo', 'PCAR3.SA': 'Consumo', 'ASAI3.SA': 'Consumo',
            
            # Utilities
            'SBSP3.SA': 'Utilities', 'CMIG4.SA': 'Utilities', 'ELET3.SA': 'Utilities',
            'ELET6.SA': 'Utilities', 'CPFE3.SA': 'Utilities', 'ENGI11.SA': 'Utilities',
            'TAEE11.SA': 'Utilities', 'EQTL3.SA': 'Utilities',
            
            # Imobiliário
            'BRCR11.SA': 'Imobiliário', 'KNRI11.SA': 'Imobiliário', 'HGLG11.SA': 'Imobiliário',
            'VISC11.SA': 'Imobiliário', 'HGBS11.SA': 'Imobiliário', 'XPLG11.SA': 'Imobiliário',
            
            # Telecomunicações
            'VIVT3.SA': 'Telecomunicações', 'TIMS3.SA': 'Telecomunicações', 'OIBR3.SA': 'Telecomunicações',
            'TELB4.SA': 'Telecomunicações',
            
            # Saúde
            'HAPV3.SA': 'Saúde', 'FLRY3.SA': 'Saúde', 'RDOR3.SA': 'Saúde', 
            'GNDI3.SA': 'Saúde', 'AALR3.SA': 'Saúde',
            
            # Transporte
            'CCRO3.SA': 'Transporte', 'RAIL3.SA': 'Transporte', 'ECOR3.SA': 'Transporte',
            'AZUL4.SA': 'Transporte', 'GOLL4.SA': 'Transporte', 'STBP3.SA': 'Transporte',
            
            # Construção
            'CYRE3.SA': 'Construção', 'EZTC3.SA': 'Construção', 'MRVE3.SA': 'Construção',
            'DIRR3.SA': 'Construção', 'TEND3.SA': 'Construção', 'EVEN3.SA': 'Construção',
            
            # Educação
            'YDUQ3.SA': 'Educação', 'COGN3.SA': 'Educação', 'SEER3.SA': 'Educação',
            
            # Tecnologia
            'TOTS3.SA': 'Tecnologia', 'CASH3.SA': 'Tecnologia', 'LVTC3.SA': 'Tecnologia',
            'NINJ3.SA': 'Tecnologia', 'IFCM3.SA': 'Tecnologia'
        }
        return sector_mapping
    except Exception as e:
        print(f"Erro ao mapear setores: {e}")
        return {}

def fetch_stock_data(stock_code, max_retries=3, loading_screen=None):
    """Obtém dados históricos de uma ação específica com mecanismo de retry"""
    retries = 0
    
    # Adicionar sufixo .SA se não estiver presente
    if not stock_code.endswith('.SA'):
        stock_code = f"{stock_code}.SA"
    
    while retries < max_retries:
        try:
            # Adicionar delay aleatório para evitar bloqueios de API
            time.sleep(0.5 + random.random())
            
            # Define o período de um ano até hoje
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Suprimir as mensagens de erro do yfinance
            import logging
            logging.getLogger('yfinance').setLevel(logging.ERROR)
            
            # Buscar dados usando yfinance
            stock_data = yf.download(
                stock_code, 
                start=start_date, 
                end=end_date, 
                progress=False,
                ignore_tz=True  # Ignora problemas de timezone
            )
            
            if stock_data.empty:
                raise Exception(f"Nenhum dado disponível para {stock_code}")
                
            return stock_data
                
        except Exception as e:
            retries += 1
            delay = 2 ** retries  # Backoff exponencial
            log_message = f"Tentativa {retries} falhou para {stock_code}: {str(e)}. Aguardando {delay}s..."
            print(log_message)
            if loading_screen:
                loading_screen.log(log_message)
            time.sleep(delay)
            
            # Se for erro 404, não insistir
            if "404" in str(e):
                log_message = f"Ação {stock_code} não encontrada (erro 404). Pulando..."
                print(log_message)
                if loading_screen:
                    loading_screen.log(log_message)
                break
    
    log_message = f"Erro ao obter dados da ação {stock_code} após {max_retries} tentativas."
    print(log_message)
    if loading_screen:
        loading_screen.log(log_message)
    return None

def calculate_returns(stock_data):
    """Calcula retornos diários, semanais, mensais e anuais para uma ação"""
    # Código existente mantido sem alterações
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

def get_stock_performance_data(loading_screen=None):
    """Obtém dados de desempenho para as principais ações da B3"""
    sectors = get_stock_sectors()
    
    performance_data = []
    
    # Processar todas as ações, organizadas em lotes
    stock_codes_with_sectors = list(sectors.keys())
    
    batch_size = 15
    total_batches = (len(stock_codes_with_sectors) + batch_size - 1) // batch_size
    
    log_message = f"Buscando dados para {len(stock_codes_with_sectors)} ações..."
    print(log_message)
    if loading_screen:
        loading_screen.log(log_message)
    
    successful_stocks = 0
    failed_stocks = []
    
    try:
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(stock_codes_with_sectors))
            current_batch = stock_codes_with_sectors[start_idx:end_idx]
            
            log_message = f"Processando lote {batch_idx + 1} de {total_batches} ({start_idx+1}-{end_idx} de {len(stock_codes_with_sectors)})"
            print(log_message)
            if loading_screen:
                loading_screen.log(log_message)
                
            # Atualizar o progresso
            if loading_screen:
                loading_screen.update_progress(batch_idx + 1, total_batches)
            
            for stock_code in current_batch:
                try:
                    # Remover o sufixo .SA para exibição no dashboard
                    display_code = stock_code.replace('.SA', '')
                    
                    log_message = f"Obtendo dados para {display_code}..."
                    print(log_message)
                    if loading_screen:
                        loading_screen.log(log_message)
                        
                    stock_data = fetch_stock_data(stock_code, loading_screen=loading_screen)
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
                        log_message = f"Dados processados com sucesso para {display_code}"
                        print(log_message)
                        if loading_screen:
                            loading_screen.log(log_message)
                        successful_stocks += 1
                    else:
                        failed_stocks.append(display_code)
                except Exception as e:
                    log_message = f"Erro processando ação {stock_code.replace('.SA', '')}: {e}"
                    print(log_message)
                    if loading_screen:
                        loading_screen.log(log_message)
                    failed_stocks.append(stock_code.replace('.SA', ''))
    except Exception as e:
        # Capturar exceções gerais durante o processamento em lote
        log_message = f"Erro durante o processamento: {e}"
        print(log_message)
        if loading_screen:
            loading_screen.log(log_message)
    
    # Resumo final
    log_message = f"\nProcessamento concluído: {successful_stocks} ações com sucesso, {len(failed_stocks)} falhas."
    print(log_message)
    if loading_screen:
        loading_screen.log(log_message)
        
    if failed_stocks:
        log_message = f"Ações com falha: {', '.join(failed_stocks)}"
        print(log_message)
        if loading_screen:
            loading_screen.log(log_message)
    
    # Atualizar progresso para 100% ao finalizar
    if loading_screen:
        loading_screen.update_progress(total_batches, total_batches)
    
    # SEMPRE retornar um DataFrame, mesmo que vazio
    return pd.DataFrame(performance_data)