# simple_signal_test.py
"""
Простой тест сигналов без XGBoost
"""

import asyncio
from api_client import UnifiedFastClient
from telegram_bot_ultimate import TelegramBot
import config
import random

async def test_signal():
    print("="*60)
    print("SIMPLE SIGNAL TEST")
    print("="*60)
    
    # Создаем тестовое сообщение
    test_message = f"""
⚽ TEST SIGNAL
Test match vs Test Team
Minute: 45'

Probability: 75.0%
Confidence: HIGH

Test message from bot - {__import__('datetime').datetime.now().strftime('%H:%M:%S')}
"""
    
    print("\nSending test signal to Telegram...")
    bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
    
    result = bot.send_message(test_message)
    print(f"Message added to queue: {result}")
    
    # Ждем отправки
    print("Waiting 5 seconds for delivery...")
    await asyncio.sleep(5)
    
    bot.stop()
    
    print("\n✅ Test complete! Check Telegram channel.")

if __name__ == "__main__":
    asyncio.run(test_signal())