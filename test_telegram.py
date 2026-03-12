# test_telegram.py
import asyncio
from telegram import Bot
import config

async def test_telegram():
    """Тестирует отправку сообщения в Telegram"""
    
    bot = Bot(token=config.BOT_TOKEN)
    
    try:
        # Проверяем подключение
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username}")
        
        # Отправляем тестовое сообщение
        await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text="🔔 **Тестовое сообщение**\n\nЕсли вы это видите, бот работает правильно!",
            parse_mode='Markdown'
        )
        print(f"✅ Тестовое сообщение отправлено в канал {config.CHANNEL_ID}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram())