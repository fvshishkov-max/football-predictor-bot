# view_live_predictions.py
"""
Просмотр live предсказаний в реальном времени
Запуск: python view_live_predictions.py
"""

import asyncio
import json
from datetime import datetime
from api_client import UnifiedFastClient
from predictor import Predictor

async def view_live():
    print("="*80)
    print("📊 LIVE ПРЕДСКАЗАНИЯ")
    print(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    client = UnifiedFastClient()
    predictor = Predictor()
    
    matches = await client.get_live_matches()
    print(f"\n📋 Найдено live матчей: {len(matches)}")
    
    if not matches:
        print("❌ Нет live матчей")
        return
    
    print("\n" + "="*80)
    print(f"{'Статус':<8} {'Минута':<6} {'Счет':<6} {'Вероятность':<12} {'Уверенность':<12} {'Матч'}")
    print("="*80)
    
    predictions_data = []
    
    for match in matches:
        home = match.home_team.name if match.home_team else "?"
        away = match.away_team.name if match.away_team else "?"
        minute = match.minute or 0
        score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        # Получаем статистику
        stats = await client.get_match_statistics(match)
        if stats:
            match.stats = stats
        
        # Получаем предсказание
        prediction = predictor.predict_match(match)
        prob = prediction.get('goal_probability', 0) * 100
        conf = prediction.get('confidence_level', 'UNKNOWN')
        signal = prediction.get('signal') is not None
        
        status = "🔴 СИГНАЛ" if signal else ("🟡 ВЫСОКИЙ" if prob > 45 else "⚪ НИЗКИЙ")
        
        predictions_data.append({
            'home': home,
            'away': away,
            'minute': minute,
            'score': score,
            'prob': prob,
            'conf': conf,
            'signal': signal
        })
        
        print(f"{status:<8} {minute:<6} {score:<6} {prob:<11.1f}% {conf:<12} {home[:20]} vs {away[:20]}")
    
    print("="*80)
    
    # Статистика
    signals = [p for p in predictions_data if p['signal']]
    print(f"\n📊 Статистика:")
    print(f"  • Всего матчей: {len(predictions_data)}")
    print(f"  • Сигналов: {len(signals)}")
    print(f"  • Средняя вероятность сигналов: {sum(s['prob'] for s in signals)/len(signals):.1f}%" if signals else "Нет сигналов")
    
    if signals:
        print(f"\n🔔 СИГНАЛЫ:")
        for s in signals:
            print(f"  🔴 {s['home']} vs {s['away']} ({s['minute']}') - {s['prob']:.1f}% ({s['conf']})")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(view_live())