import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StockDataCache:
    def __init__(self, cache_dir="cache", max_cache_age_hours=8):
        """
        Inicializa o gerenciador de cache para dados de ações
        
        Args:
            cache_dir: Diretório onde o cache será armazenado
            max_cache_age_hours: Idade máxima do cache em horas antes de ser considerado obsoleto
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "stock_data_cache.pkl")
        self.max_cache_age = timedelta(hours=max_cache_age_hours)
        
        # Cache em memória
        self.memory_cache = None
        self.memory_cache_time = None
        
        # Criar diretório de cache se não existir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cached_data(self):
        """
        Recupera dados do cache se estiverem válidos
        
        Returns:
            DataFrame ou None: Os dados de ações ou None se o cache não for válido
        """
        # Primeiro, verificar cache em memória
        if self.memory_cache is not None and self.memory_cache_time is not None:
            if (datetime.now() - self.memory_cache_time) <= self.max_cache_age:
                logging.info("Usando cache em memória")
                return self.memory_cache

        if not os.path.exists(self.cache_file):
            logging.info("Cache não encontrado")
            return None
            
        # Verificar idade do arquivo
        file_time = datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        now = datetime.now()
        
        # Se o arquivo for de hoje e não for muito antigo
        if (now - file_time) <= self.max_cache_age:
            try:
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    
                logging.info(f"Dados carregados do cache gerado em: {file_time}")
                
                # Se carregou do disco, armazenar em memória também
                if cache_data is not None:
                    self.memory_cache = cache_data
                    self.memory_cache_time = datetime.now()
                
                return cache_data
            except Exception as e:
                logging.error(f"Erro ao carregar cache: {str(e)}")
                return None
        else:
            logging.info(f"Cache expirado. Cache de {file_time}, agora é {now}")
            return None
    
    def save_data_to_cache(self, data):
        """
        Salva os dados no cache
        
        Args:
            data: DataFrame contendo os dados de ações
        """
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            logging.info(f"Dados salvos no cache: {len(data)} ações")
            
            # Salvar em memória também
            self.memory_cache = data
            self.memory_cache_time = datetime.now()
            
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {str(e)}")
            return False
    
    def clear_cache(self):
        """Remove o arquivo de cache"""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            logging.info("Cache removido")
        # Limpar cache em memória também
        self.memory_cache = None
        self.memory_cache_time = None