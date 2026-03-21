# force_signal_test.py
"""
Принудительная отправка сигнала для матча с высокой вероятностью
"""

import asyncio
from api_client import UnifiedFastClient
from predictor import Predictor
from telegram_bot_ultimate import TelegramBot
import config

async def force_signal():
    client = UnifiedFastClient()
    predictor = Predictor()
    
    print("Finding first match with >46% probability...")
    matches = await client.get_live_matches()
    
    high_prob_match = None
    for match in matches:
        pred = predictor.predict_match(match)
        prob = pred.get('goal_probability', 0) * 100
        if prob > 46:
            high_prob_match = match
            print(f"Found: {match.home_team.name} vs {match.away_team.name} - {prob:.1f}%")
            break
    
    if high_prob_match:
        print("\nGenerating signal...")
        signal = predictor.analyze_live_match(high_prob_match)
        
        if signal:
            message = signal.get('message')
            print(f"Message: {message[:200]}...")
            
            print("\nSending to Telegram...")
            bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
            bot.send_message(message)
            
            import time
            time.sleep(3)
            bot.stop()
            
            print("✅ Signal sent! Check Telegram channel.")
        else:
            print("No signal generated")
    else:
        print("No match with >46% probability found")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(force_signal())