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