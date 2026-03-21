# check_telegram.py
"""
Проверка, отправляются ли сигналы в Telegram
"""

import json
import os

def check_telegram_methods():
    """Проверяет, есть ли метод send_message в telegram_bot_ultimate.py"""
    
    with open('telegram_bot_ultimate.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("="*60)
    print("TELEGRAM BOT CHECK")
    print("="*60)
    
    # Проверяем наличие метода send_message
    if 'def send_message' in content:
        print("✅ send_message method found")
    else:
        print("❌ send_message method NOT found!")
    
    # Проверяем send_goal_signal
    if 'def send_goal_signal' in content:
        print("✅ send_goal_signal method found")
    else:
        print("❌ send_goal_signal method NOT found!")
    
    # Проверяем вызов в app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    if 'self.telegram_bot.send_message' in app_content:
        print("✅ app.py uses send_message")
    elif 'self.telegram_bot.send_goal_signal' in app_content:
        print("✅ app.py uses send_goal_signal")
    else:
        print("❌ No telegram send method found in app.py!")

def test_send():
    """Тест отправки сообщения в Telegram"""
    
    try:
        from telegram_bot_ultimate import TelegramBot
        import config
        
        print("\n" + "="*60)
        print("TEST SENDING MESSAGE")
        print("="*60)
        
        bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
        
        test_message = "Test message from bot - " + __import__('datetime').datetime.now().strftime('%H:%M:%S')
        
        print(f"Sending: {test_message}")
        
        # Пробуем отправить
        if hasattr(bot, 'send_message'):
            result = bot.send_message(test_message)
            print(f"Result: {result}")
        elif hasattr(bot, 'send_goal_signal'):
            result = bot.send_goal_signal(None, None, test_message)
            print(f"Result: {result}")
        else:
            print("No send method found!")
        
        bot.stop()
        
    except Exception as e:
        print(f"Error: {e}")

def list_signals():
    """Показывает сигналы, которые должны были отправиться"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        preds = data.get('predictions', [])
    
    signals = [p for p in preds if p.get('goal_probability', 0) > 0.46]
    
    print("\n" + "="*60)
    print(f"SIGNALS THAT SHOULD BE SENT ({len(signals)})")
    print("="*60)
    
    for pred in signals[-10:]:
        ts = pred.get('timestamp', '')[:16]
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        print(f"  {ts} | {minute:2d}' | {home} vs {away} | {prob:.1f}%")

if __name__ == "__main__":
    check_telegram_methods()
    list_signals()
    test_send()