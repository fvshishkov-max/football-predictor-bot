# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "8117632870:AAHXkrXSj3m317Djb548KdNKzv7DD3WLKzM")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1001960458800")

# SStats API
SSTATS_API_KEY = os.getenv("SSTATS_API_KEY", "k0f69qjmqx4gs8a8")
SSTATS_BASE_URL = "https://api.sstats.net"
USE_MOCK_DATA = False  # False для реального API, True для тестовых данных

# Настройки
TIMEZONE = 3
UPDATE_INTERVAL = 30  # секунд

# Цветовая схема для UI
COLORS = {
    'bg': '#1a2a3a',
    'fg': '#ffffff',
    'accent': '#2a9d8f',
    'warning': '#e76f51',
    'success': '#2a9d8f',
    'info': '#e9c46a',
    'live': '#e63946',
    'prematch': '#4a6fa5',
    'card_bg': '#2a3a4a',
    'profit_high': '#00ff00',
    'profit_medium': '#ffff00',
    'profit_low': '#ff6b6b',
    'alert': '#ff1493',
    'selected': '#4169e1'
}