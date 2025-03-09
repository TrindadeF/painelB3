import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import time
import random
import logging
import requests
import threading

# Importar o gerenciador de cache
from .stock_cache import StockDataCache

# Configurar logging
logging.getLogger('yfinance').setLevel(logging.ERROR)

# Lista de ações ignoradas (deslistadas ou com problemas)
IGNORED_STOCKS = ['LCAM3.SA', 'HAPV3.SA', 'VULC3.SA', 'GUAR3.SA']

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
    """Retorna um dicionário completo que mapeia ações aos seus respectivos setores da B3"""
    try:
        sector_mapping = {
            # Setor Financeiro
            'ITUB4.SA': 'Financeiro',
            'BBDC4.SA': 'Financeiro',
            'BBAS3.SA': 'Financeiro',
            'SANB11.SA': 'Financeiro',
            'B3SA3.SA': 'Financeiro',
            'BPAC11.SA': 'Financeiro',
            'BBSE3.SA': 'Financeiro',
            'CIEL3.SA': 'Financeiro',
            'IRBR3.SA': 'Financeiro',
            'SULA11.SA': 'Financeiro',
            'PSSA3.SA': 'Financeiro',
            'BPAN4.SA': 'Financeiro',
            'ABCB4.SA': 'Financeiro',
            'BRSR6.SA': 'Financeiro',
            
            # Materiais Básicos
            'VALE3.SA': 'Materiais Básicos',
            'SUZB3.SA': 'Materiais Básicos',
            'KLBN11.SA': 'Materiais Básicos',
            'CSNA3.SA': 'Materiais Básicos',
            'GGBR4.SA': 'Materiais Básicos',
            'GOAU4.SA': 'Materiais Básicos',
            'BRAP4.SA': 'Materiais Básicos',
            'USIM5.SA': 'Materiais Básicos',
            'DXCO3.SA': 'Materiais Básicos',
            'BRKM5.SA': 'Materiais Básicos',
            'UNIP6.SA': 'Materiais Básicos',
            
            # Petróleo, Gás e Biocombustíveis
            'PETR3.SA': 'Petróleo e Gás',
            'PETR4.SA': 'Petróleo e Gás',
            'PRIO3.SA': 'Petróleo e Gás',
            'CSAN3.SA': 'Petróleo e Gás',
            'VBBR3.SA': 'Petróleo e Gás',
            'RAPT4.SA': 'Petróleo e Gás',
            'RRRP3.SA': 'Petróleo e Gás',
            'UGPA3.SA': 'Petróleo e Gás',
            
            # Utilities (Utilidade Pública)
            'SBSP3.SA': 'Utilidade Pública',
            'ELET3.SA': 'Utilidade Pública',
            'ELET6.SA': 'Utilidade Pública',
            'CMIG4.SA': 'Utilidade Pública',
            'CPFE3.SA': 'Utilidade Pública',
            'ENGI11.SA': 'Utilidade Pública',
            'ENEV3.SA': 'Utilidade Pública',
            'EGIE3.SA': 'Utilidade Pública',
            'EQTL3.SA': 'Utilidade Pública',
            'TAEE11.SA': 'Utilidade Pública',
            'TIET11.SA': 'Utilidade Pública',
            'NEOE3.SA': 'Utilidade Pública',
            'ALUP11.SA': 'Utilidade Pública',
            'CSMG3.SA': 'Utilidade Pública',
            'SAPR11.SA': 'Utilidade Pública',
            'GEPA4.SA': 'Utilidade Pública',
            
            # Consumo não Cíclico
            'ABEV3.SA': 'Consumo não Cíclico',
            'NTCO3.SA': 'Consumo não Cíclico',
            'JBSS3.SA': 'Consumo não Cíclico',
            'MRFG3.SA': 'Consumo não Cíclico',
            'BRFS3.SA': 'Consumo não Cíclico',
            'SMTO3.SA': 'Consumo não Cíclico',
            'BEEF3.SA': 'Consumo não Cíclico',
            'CAML3.SA': 'Consumo não Cíclico',
            'MDIA3.SA': 'Consumo não Cíclico',
            'CRFB3.SA': 'Consumo não Cíclico',
            'PCAR3.SA': 'Consumo não Cíclico',
            'ASAI3.SA': 'Consumo não Cíclico',
            'SLCE3.SA': 'Consumo não Cíclico',
            
            # Consumo Cíclico
            'LREN3.SA': 'Consumo Cíclico',
            'MGLU3.SA': 'Consumo Cíclico',
            'AMER3.SA': 'Consumo Cíclico',
            'VVAR3.SA': 'Consumo Cíclico',
            'LWSA3.SA': 'Consumo Cíclico',
            'HGTX3.SA': 'Consumo Cíclico',
            'SOMA3.SA': 'Consumo Cíclico',
            'CEAB3.SA': 'Consumo Cíclico',
            'AMAR3.SA': 'Consumo Cíclico',
            'CVCB3.SA': 'Consumo Cíclico',
            'MOVI3.SA': 'Consumo Cíclico',
            'VAMO3.SA': 'Consumo Cíclico',
            'RENT3.SA': 'Consumo Cíclico',
            'LCAM3.SA': 'Consumo Cíclico',
            'PETZ3.SA': 'Consumo Cíclico',
            'ARML3.SA': 'Consumo Cíclico',
            'SBFG3.SA': 'Consumo Cíclico',
            'ALPA4.SA': 'Consumo Cíclico',
            'GRND3.SA': 'Consumo Cíclico',
            'GUAR3.SA': 'Consumo Cíclico',
            'VULC3.SA': 'Consumo Cíclico',
            
            # Saúde
            'RDOR3.SA': 'Saúde',
            'HAPV3.SA': 'Saúde',
            'FLRY3.SA': 'Saúde',
            'QUAL3.SA': 'Saúde',
            'PNVL3.SA': 'Saúde',
            'HYPE3.SA': 'Saúde',
            'DASA3.SA': 'Saúde',
            'AALR3.SA': 'Saúde',
            'MATD3.SA': 'Saúde',
            'ODPV3.SA': 'Saúde',
            
            # Tecnologia da Informação
            'TOTS3.SA': 'Tecnologia',
            'CASH3.SA': 'Tecnologia',
            'LVTC3.SA': 'Tecnologia',
            'NINJ3.SA': 'Tecnologia',
            'IFCM3.SA': 'Tecnologia',
            'SQIA3.SA': 'Tecnologia',
            'POSI3.SA': 'Tecnologia',
            'LINX3.SA': 'Tecnologia',
            
            # Bens Industriais
            'WEGE3.SA': 'Bens Industriais',
            'EMBR3.SA': 'Bens Industriais',
            'RAIL3.SA': 'Bens Industriais',
            'TGMA3.SA': 'Bens Industriais',
            'INTB3.SA': 'Bens Industriais',
            'MYPK3.SA': 'Bens Industriais',
            'FRAS3.SA': 'Bens Industriais',
            'TUPY3.SA': 'Bens Industriais',
            'KEPL3.SA': 'Bens Industriais',
            'LEVE3.SA': 'Bens Industriais',
            'METAL3.SA': 'Bens Industriais',
            'ROMI3.SA': 'Bens Industriais',
            'EALT4.SA': 'Bens Industriais',
            
            # Comunicações
            'VIVT3.SA': 'Comunicações',
            'TIMS3.SA': 'Comunicações',
            'TELB4.SA': 'Comunicações',
            'OIBR3.SA': 'Comunicações',
            'OIBR4.SA': 'Comunicações',
            
            # Transporte e Logística
            'CCRO3.SA': 'Transporte',
            'ECOR3.SA': 'Transporte',
            'AZUL4.SA': 'Transporte',
            'GOLL4.SA': 'Transporte',
            'STBP3.SA': 'Transporte',
            'HBSA3.SA': 'Transporte',
            'PSSA3.SA': 'Transporte',
            'WEST3.SA': 'Transporte',
            'TPIS3.SA': 'Transporte',
            
            # Imobiliário / Construção Civil
            'CYRE3.SA': 'Imobiliário',
            'EZTC3.SA': 'Imobiliário',
            'MRVE3.SA': 'Imobiliário',
            'DIRR3.SA': 'Imobiliário',
            'TEND3.SA': 'Imobiliário',
            'EVEN3.SA': 'Imobiliário',
            'JHSF3.SA': 'Imobiliário',
            'GFSA3.SA': 'Imobiliário',
            'HBOR3.SA': 'Imobiliário',
            
            # Fundos Imobiliários (mesmo não sendo ações, são populares)
            'BRCR11.SA': 'Fundos Imobiliários',
            'KNRI11.SA': 'Fundos Imobiliários',
            'HGLG11.SA': 'Fundos Imobiliários',
            'VISC11.SA': 'Fundos Imobiliários',
            'HGBS11.SA': 'Fundos Imobiliários',
            'XPLG11.SA': 'Fundos Imobiliários',
            'XPML11.SA': 'Fundos Imobiliários',
            'MXRF11.SA': 'Fundos Imobiliários',
            'BCFF11.SA': 'Fundos Imobiliários',
            'BBPO11.SA': 'Fundos Imobiliários',
            'HFOF11.SA': 'Fundos Imobiliários',
            
            # Educação
            'YDUQ3.SA': 'Educação',
            'COGN3.SA': 'Educação',
            'SEER3.SA': 'Educação',
            'AESB3.SA': 'Educação',
            'BAHI3.SA': 'Educação',
        }
        return sector_mapping
    except Exception as e:
        print(f"Erro ao mapear setores: {e}")
        return {}

# Modificar a função fetch_stock_data para buscar apenas dados necessários
def fetch_stock_data(stock_code, max_retries=3, loading_screen=None):
    """Obtém dados históricos de uma ação específica com mecanismo de retry"""
    
    # Verificar se a ação está na lista de ignoradas
    if stock_code in IGNORED_STOCKS:
        if loading_screen:
            loading_screen.log(f"Ignorando {stock_code} (ação deslistada ou com problemas conhecidos)")
        return None
    
    retries = 0
    
    # Adicionar sufixo .SA se não estiver presente
    if not stock_code.endswith('.SA'):
        stock_code = f"{stock_code}.SA"
    
    while retries < max_retries:
        try:
            # Reduzir delay para melhorar performance
            time.sleep(0.2)  # Reduzido de 0.5 + random
            
            # Define o período mais curto (3 meses é suficiente para a maioria das métricas)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Reduzido de 365 para 90 dias
            
            # Buscar dados usando yfinance - com período mais curto
            stock_data = yf.download(
                stock_code, 
                start=start_date, 
                end=end_date, 
                progress=False,
                ignore_tz=True
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
    """Calcula os retornos de uma ação para diferentes períodos"""
    try:
        # Garantir que estamos trabalhando com uma única coluna 'Close'
        if isinstance(stock_data['Close'], pd.DataFrame):
            close_values = stock_data['Close'].iloc[:, 0]  # Pegar apenas a primeira coluna
        else:
            close_values = stock_data['Close']
            
        # Calcular retornos com fill_method=None para evitar o aviso de depreciação
        daily_return = close_values.pct_change(periods=1, fill_method=None).iloc[-1]
        weekly_return = close_values.pct_change(periods=5, fill_method=None).iloc[-1]
        monthly_return = close_values.pct_change(periods=20, fill_method=None).iloc[-1]
        quarterly_return = close_values.pct_change(periods=60, fill_method=None).iloc[-1]
        yearly_return = close_values.pct_change(periods=252, fill_method=None).iloc[-1]
        
        # Converter para porcentagem e retornar
        return {
            'daily': float(daily_return * 100) if not pd.isna(daily_return) else 0.0,
            'weekly': float(weekly_return * 100) if not pd.isna(weekly_return) else 0.0,
            'monthly': float(monthly_return * 100) if not pd.isna(monthly_return) else 0.0,
            'quarterly': float(quarterly_return * 100) if not pd.isna(quarterly_return) else 0.0,
            'yearly': float(yearly_return * 100) if not pd.isna(yearly_return) else 0.0
        }
    except Exception as e:
        print(f"Erro ao calcular retornos: {str(e)}")
        # Retornar valores vazios em caso de erro
        return {
            'daily': 0.0,
            'weekly': 0.0,
            'monthly': 0.0,
            'quarterly': 0.0,
            'yearly': 0.0
        }

def process_stock_thread(stock_code, results, index, stock_sectors, loading_screen=None):
    """Função para processar uma ação em uma thread separada"""
    try:
        # Verificar se a ação está na lista de ignoradas
        if stock_code in IGNORED_STOCKS:
            if loading_screen:
                loading_screen.log(f"Ignorando {stock_code} (ação deslistada ou com problemas conhecidos)")
            return
            
        if loading_screen:
            loading_screen.log(f"Processando {stock_code}")
        
        # Obter dados históricos
        historical_data = fetch_stock_data(stock_code, loading_screen=loading_screen)
        if historical_data is None or historical_data.empty:
            return
        
        # Verificar se temos uma série temporal suficiente
        if len(historical_data) < 2:
            if loading_screen:
                loading_screen.log(f"Dados insuficientes para {stock_code}. Necessários pelo menos 2 dias de dados.")
            return
            
        # Calcular retornos
        returns = calculate_returns(historical_data)
        
        # Extrair dados do último dia
        latest_data = historical_data.iloc[-1]
        
        # Criar dicionário com dados da ação
        stock_data = {
            'code': stock_code.replace('.SA', ''),
            'name': stock_code.replace('.SA', ''),
            'sector': stock_sectors.get(stock_code, 'Outros'),
            'current_price': float(latest_data['Close']),
            'open_price': float(latest_data['Open']),
            'high_price': float(latest_data['High']),
            'low_price': float(latest_data['Low']),
            'close_price': float(latest_data['Close']),
            'volume': float(latest_data['Volume']),
            'daily_return': returns['daily'],
            'weekly_return': returns['weekly'],
            'monthly_return': returns['monthly'],
            'yearly_return': returns['yearly'],
            'ytd_return': ((float(latest_data['Close']) / float(historical_data['Close'].iloc[0])) - 1) * 100 if len(historical_data) > 0 else 0.0
        }
        
        # Armazenar no array de resultados
        results[index] = stock_data
        
    except Exception as e:
        if loading_screen:
            loading_screen.log(f"Erro ao processar {stock_code}: {str(e)}")
        print(f"Erro ao processar {stock_code}: {str(e)}")

def get_stock_performance_data(loading_screen=None):
    """Versão otimizada para obter dados de desempenho das ações da B3"""
    # Inicializar gerenciador de cache
    cache = StockDataCache()
    
    # Tentar carregar do cache primeiro
    if loading_screen:
        loading_screen.log("Verificando dados em cache...")
    
    cached_data = cache.get_cached_data()
    if cached_data is not None:
        if loading_screen:
            loading_screen.log(f"Dados encontrados em cache: {len(cached_data)} ações")
            loading_screen.update_progress(100, 100)
        return cached_data

    if loading_screen:
        loading_screen.log("Cache não disponível ou expirado. Buscando dados atualizados...")
    
    try:
        # Obter lista de ações - limite o número para melhorar a performance
        stock_sectors = get_stock_sectors()
        
        # Obter apenas as ações mais importantes - limite a 50 ou 100 para melhor desempenho
        # Você pode priorizar as ações mais líquidas do Ibovespa
        stock_list = list(stock_sectors.keys())[:100]  # Limitar a 100 ações
        
        if loading_screen:
            loading_screen.log(f"Lista de ações obtida: {len(stock_list)} ações")
        
        # Processar ações em lotes
        batch_size = 5  # Processar 5 ações por vez
        batches = [stock_list[i:i+batch_size] for i in range(0, len(stock_list), batch_size)]
        
        all_data = []
        total_processed = 0
        
        for batch_idx, batch in enumerate(batches):
            batch_data = []
            # Criar threads para processamento paralelo do lote
            threads = []
            results = [None] * len(batch)
            
            for i, stock_code in enumerate(batch):
                # Criar thread para cada ação no lote
                t = threading.Thread(
                    target=process_stock_thread, 
                    args=(stock_code, results, i, stock_sectors, loading_screen)
                )
                threads.append(t)
                t.start()
            
            # Esperar todas as threads terminarem
            for t in threads:
                t.join()
            
            # Adicionar resultados válidos aos dados
            for result in results:
                if result:
                    all_data.append(result)
            
            total_processed += len(batch)
            if loading_screen:
                loading_screen.update_progress(total_processed, len(stock_list))
        
        # Criar DataFrame com todos os dados
        performance_data = pd.DataFrame(all_data)
        
        # Salvar no cache após obter os dados
        if performance_data is not None and not performance_data.empty:
            cache.save_data_to_cache(performance_data)
            if loading_screen:
                loading_screen.log(f"Dados salvos em cache: {len(performance_data)} ações")
        
        return performance_data
        
    except Exception as e:
        if loading_screen:
            loading_screen.log(f"Erro ao buscar dados: {str(e)}")
        return None