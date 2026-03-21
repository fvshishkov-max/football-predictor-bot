# check_bot_memory.py
"""
Проверка, что бот видит live матчи и генерирует предсказания
Запуск: python check_bot_memory.py
"""

import asyncio
import json
import sys
from datetime import datetime

async def check_memory():
    print("="*80)
    print("🔍 ПРОВЕРКА ПАМЯТИ БОТА")
    print("="*80)
    
    from api_client import UnifiedFastClient
    from predictor import Predictor
    
    client = UnifiedFastClient()
    predictor = Predictor()
    
    print("\n1. Получение live матчей...")
    matches = await client.get_live_matches()
    print(f"   Найдено матчей: {len(matches)}")
    
    if matches:
        print("\n2. Первые 5 матчей:")
        for m in matches[:5]:
            home = m.home_team.name if m.home_team else "?"
            away = m.away_team.name if m.away_team else "?"
            minute = m.minute or 0
            score = f"{m.home_score or 0}:{m.away_score or 0}"
            print(f"   {home} vs {away} ({minute}') - {score}")
    
    print("\n3. Генерация предсказаний...")
    signals = 0
    for match in matches[:10]:  # Проверяем первые 10
        signal = predictor.analyze_live_match(match)
        if signal:
            signals += 1
            print(f"   ✅ Сигнал для {match.home_team.name} vs {match.away_team.name}")
    
    print(f"\n📊 Сигналов из {min(10, len(matches))} матчей: {signals}")
    print(f"📊 Предсказаний в памяти: {len(predictor.predictions_history)}")
    
    # Принудительно сохраняем
    if len(predictor.predictions_history) > 0:
        predictor.save_predictions()
        print(f"✅ Сохранено в файл")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(check_memory())