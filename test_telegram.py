# test_telegram.py
"""
Тестирование отправки сообщений в Telegram с ротацией прокси
"""

import logging
import time
from telegram_bot import TelegramBot
from models import Match, Team

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram():
    """Тестирует отправку сообщений"""
    
    print("\n" + "="*60)
    print("📨 ТЕСТИРОВАНИЕ ОТПРАВКИ В TELEGRAM С ПРОКСИ")
    print("="*60)
    
    # Создаем тестовый матч
    match = Match(
        id=99999,
        home_team=Team(id=1, name="Test Home"),
        away_team=Team(id=2, name="Test Away"),
        minute=30,
        home_score=1,
        away_score=0
    )
    match.probability = 87.5
    
    # Создаем бота
    bot = TelegramBot("8117632870:AAHXkrXSj3m317Djb548KdNKzv7DD3WLKzM", "-1001679913676")
    
    # Даем боту время протестировать прокси
    time.sleep(2)
    
    # Отправляем 5 тестовых сообщений
    for i in range(5):
        print(f"\n📌 Отправка теста #{i+1}")
        bot.send_goal_signal(match, None, f"⚽ Тест #{i+1} с прокси")
        time.sleep(1)
    
    print("\n⏳ Ожидание отправки (15 секунд)...")
    
    for i in range(15):
        time.sleep(1)
        stats = bot.get_stats()
        print(f"  • Секунда {i+1}: Отправлено: {stats['sent']}, Очередь: {stats['queue']}, Рабочих прокси: {stats['working_proxies']}")
    
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    stats = bot.get_stats()
    print(f"✅ Успешно отправлено: {stats['sent']}")
    print(f"❌ Ошибок: {stats['failed']}")
    print(f"📦 Осталось в очереди: {stats['queue']}")
    print(f"🔄 Рабочих прокси: {stats['working_proxies']}")
    
    if stats['proxy_usage']:
        print("\n📊 Использование прокси:")
        for name, count in stats['proxy_usage'].items():
            if count > 0:
                print(f"  {name}: {count} сообщений")
    
    print("="*60)
    
    bot.stop()

if __name__ == "__main__":
    test_telegram()