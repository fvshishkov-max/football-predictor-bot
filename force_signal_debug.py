# force_signal_debug.py
"""
Принудительная отправка сигнала для тестового матча
"""

import asyncio
from api_client import UnifiedFastClient
from predictor import Predictor
from telegram_bot_direct import TelegramBot
import config

async def force_send():
    client = UnifiedFastClient()
    predictor = Predictor()
    
    print("Getting live matches...")
    matches = await client.get_live_matches()
    
    if not matches:
        print("No matches found")
        return
    
    # Берем первый матч
    match = matches[0]
    home = match.home_team.name if match.home_team else "?"
    away = match.away_team.name if match.away_team else "?"
    minute = match.minute or 0
    
    print(f"\nAnalyzing: {home} vs {away} ({minute}')")
    
    # Получаем предсказание
    prediction = predictor.predict_match(match)
    prob = prediction.get('goal_probability', 0) * 100
    conf = prediction.get('confidence_level', 'UNKNOWN')
    
    print(f"Probability: {prob:.1f}%")
    print(f"Confidence: {conf}")
    
    # Создаем сигнал
    signal = predictor._generate_signal(
        match,
        prediction['goal_probability'],
        conf,
        prediction.get('home_stats', {}),
        prediction.get('away_stats', {})
    )
    
    if signal:
        message = signal.get('message', '')
        print(f"\nMessage: {message[:200]}...")
        
        print("\nSending to Telegram...")
        bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
        result = bot.send_message(message)
        
        if result:
            print("✅ Signal sent! Check Telegram.")
        else:
            print("❌ Failed to send")
    else:
        print("❌ No signal generated")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(force_send())