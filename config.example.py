# config.py
"""
Конфигурационный файл с новыми путями
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Telegram настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8117632870:AAHXkrXSj3m317Djb548KdNKzv7DD3WLKzM')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1001679913676')

# API ключи
SSTATS_TOKEN = os.getenv('SSTATS_TOKEN', 'k0f69qjmqx4gs8a8')
FOOTBALL_DATA_KEY = os.getenv('FOOTBALL_DATA_KEY', '5b1f5b1fbec540c1bc4b4a10d620d3ed')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '95e0af3487b211aa87b65f87a96f5646')

# Настройки API
USE_MOCK_API = os.getenv('USE_MOCK_API', 'False').lower() == 'true'  # Добавлено!

# Настройки мониторинга
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
LIVE_MATCHES_INTERVAL = int(os.getenv('LIVE_MATCHES_INTERVAL', '30'))

# Пути к данным
DATA_DIR = 'data'
PREDICTIONS_DIR = os.path.join(DATA_DIR, 'predictions')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
STATS_DIR = os.path.join(DATA_DIR, 'stats')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
BACKUPS_DIR = os.path.join(DATA_DIR, 'backups')
MODELS_DIR = os.path.join(DATA_DIR, 'models')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')

# Конкретные файлы
DB_PATH = os.path.join(HISTORY_DIR, 'matches_history.db')
CACHE_DB_PATH = os.path.join(CACHE_DIR, 'football_cache.db')
PREDICTIONS_FILE = os.path.join(PREDICTIONS_DIR, 'predictions.json')
STATS_FILE = os.path.join(STATS_DIR, 'prediction_stats.json')
MODEL_PATH = os.path.join(MODELS_DIR, 'xgboost_model.pkl')
LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

# Настройки сигналов
MIN_PROBABILITY_FOR_SIGNAL = float(os.getenv('MIN_PROBABILITY_FOR_SIGNAL', '0.46'))
SIGNAL_COOLDOWN = int(os.getenv('SIGNAL_COOLDOWN', '300'))

# Настройки анализа формы
FORM_DAYS = int(os.getenv('FORM_DAYS', '30'))
FORM_MATCHES_LIMIT = int(os.getenv('FORM_MATCHES_LIMIT', '10'))

# Настройки производительности
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))

# Создаем все папки при импорте
for dir_path in [DATA_DIR, PREDICTIONS_DIR, HISTORY_DIR, STATS_DIR, 
                 LOGS_DIR, BACKUPS_DIR, MODELS_DIR, CACHE_DIR]:
    os.makedirs(dir_path, exist_ok=True)

def validate_config():
    """Проверяет конфигурацию"""
    errors = []
    
    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN not set")
    
    if not errors:
        print("✅ Configuration loaded successfully")
        print(f"📁 Data directory: {DATA_DIR}")
        print(f"📊 Stats directory: {STATS_DIR}")
        print(f"📜 Logs directory: {LOGS_DIR}")
        print(f"🎭 USE_MOCK_API: {USE_MOCK_API}")
        return True
    else:
        for error in errors:
            print(f"❌ {error}")
        return False

if __name__ != "__main__":
    validate_config()