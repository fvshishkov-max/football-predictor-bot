# force_send_signal.py
"""
Принудительная отправка последнего сигнала в Telegram
"""

import json
import os
from telegram_bot_ultimate import TelegramBot
import config

def send_last_signal():
    """Отправляет последний сигнал в Telegram"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        preds = data.get('predictions', [])
    
    # Находим последний сигнал (>46%)
    signals = [p for p in preds if p.get('goal_probability', 0) > 0.46]
    
    if not signals:
        print("No signals found")
        return
    
    last_signal = signals[-1]
    
    home = last_signal.get('home_team', 'Unknown')
    away = last_signal.get('away_team', 'Unknown')
    prob = last_signal.get('goal_probability', 0) * 100
    minute = last_signal.get('minute', 0)
    
    message = f"""⚽ POTENTIAL GOAL!
{home} vs {away}
Score: {last_signal.get('current_score', '0:0')}
Minute: {minute}'

Probability: {prob:.1f}%
Confidence: {last_signal.get('confidence_level', 'MEDIUM')}"""
    
    print(f"Sending signal:")
    print(message)
    print("\n" + "="*40)
    
    bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
    
    if hasattr(bot, 'send_message'):
        result = bot.send_message(message)
    elif hasattr(bot, 'send_goal_signal'):
        result = bot.send_goal_signal(None, None, message)
    else:
        print("No send method!")
        result = False
    
    bot.stop()
    
    if result:
        print("✅ Signal sent!")
    else:
        print("❌ Failed to send signal")

if __name__ == "__main__":
    send_last_signal()