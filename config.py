"""
Конфигурационный файл для бота
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8117632870:AAHXkrXSj3m317Djb548KdNKzv7DD3WLKzM')
CHANNEL_ID = os.getenv('CHANNEL_ID', '-1001679913676')  # ID канала для отправки сигналов

# Настройки API
USE_MOCK_API = os.getenv('USE_MOCK_API', 'False').lower() == 'true'
SSTATS_TOKEN = os.getenv('SSTATS_TOKEN', 'k0f69qjmqx4gs8a8')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
FOOTBALL_DATA_KEY = os.getenv('FOOTBALL_DATA_KEY', '5b1f5b1fbec540c1bc4b4a10d620d3ed')

# Настройки мониторинга - УВЕЛИЧИВАЕМ ИНТЕРВАЛЫ
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '600'))  # Увеличили до 600 секунд (10 минут)
LIVE_MATCHES_INTERVAL = int(os.getenv('LIVE_MATCHES_INTERVAL', '300'))  # Увеличили до 300 секунд (5 минут)

# Настройки базы данных
DB_PATH = os.getenv('DB_PATH', 'data/matches_history.db')

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Настройки сигналов
MIN_PROBABILITY = float(os.getenv('MIN_PROBABILITY', '0.25'))
SIGNAL_COOLDOWN = int(os.getenv('SIGNAL_COOLDOWN', '300'))

# Настройки анализа формы
FORM_DAYS = int(os.getenv('FORM_DAYS', '30'))
FORM_MATCHES_LIMIT = int(os.getenv('FORM_MATCHES_LIMIT', '10'))

# Проверка обязательных переменных
def validate_config():
    """Проверяет наличие обязательных переменных конфигурации"""
    errors = []
    
    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN не установлен")
    
    if not errors:
        print("✅ Конфигурация загружена успешно")
        print(f"📱 TELEGRAM_TOKEN: {TELEGRAM_TOKEN[:10]}...")
        print(f"📢 CHANNEL_ID: {CHANNEL_ID}")
        print(f"🔑 SSTATS_TOKEN: {SSTATS_TOKEN[:5] if SSTATS_TOKEN else 'не указан'}...")
        print(f"🎭 USE_MOCK_API: {USE_MOCK_API}")
        print(f"⏱ CHECK_INTERVAL: {CHECK_INTERVAL}с (10 минут)")
        return True
    else:
        for error in errors:
            print(f"❌ {error}")
        return False

# Автоматически проверяем конфигурацию при импорте
if __name__ != "__main__":
    validate_config()