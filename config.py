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
USE_MOCK_API = os.getenv('USE_MOCK_API', 'False').lower() == 'true'  # Использовать мок API вместо реального
SSTATS_TOKEN = os.getenv('SSTATS_TOKEN', 'k0f69qjmqx4gs8a8')  # Токен для SStats API
FOOTBALL_DATA_KEY = os.getenv('FOOTBALL_DATA_KEY', '5b1f5b1fbec540c1bc4b4a10d620d3ed')  # Ключ для Football-Data.org

# Настройки мониторинга
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '600'))  # Интервал проверки матчей в секундах (10 минут)
LIVE_MATCHES_INTERVAL = int(os.getenv('LIVE_MATCHES_INTERVAL', '60'))  # Интервал обновления live матчей

# Настройки базы данных
DB_PATH = os.getenv('DB_PATH', 'data/matches_history.db')  # Путь к базе данных

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Настройки сигналов
MIN_PROBABILITY_FOR_SIGNAL = float(os.getenv('MIN_PROBABILITY_FOR_SIGNAL', '0.46'))  # Минимальная вероятность для отправки сигнала (46%)
SIGNAL_COOLDOWN = int(os.getenv('SIGNAL_COOLDOWN', '300'))  # Время между сигналами для одного матча (сек)

# Настройки анализа формы
FORM_DAYS = int(os.getenv('FORM_DAYS', '30'))  # Количество дней для анализа формы
FORM_MATCHES_LIMIT = int(os.getenv('FORM_MATCHES_LIMIT', '10'))  # Максимум матчей для анализа формы

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
        print(f"🔑 FOOTBALL_DATA_KEY: {FOOTBALL_DATA_KEY[:5] if FOOTBALL_DATA_KEY else 'не указан'}...")
        print(f"🎯 MIN_PROBABILITY: {MIN_PROBABILITY_FOR_SIGNAL*100:.0f}%")
        print(f"🎭 USE_MOCK_API: {USE_MOCK_API}")
        return True
    else:
        for error in errors:
            print(f"❌ {error}")
        return False

# Автоматически проверяем конфигурацию при импорте
if __name__ != "__main__":
    validate_config()