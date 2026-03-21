# check_goals.py
"""
Проверка, были ли голы в предсказанных матчах
Запуск: python check_goals.py
"""

import json
from datetime import datetime, timedelta

def check_goals():
    """Проверяет, были ли голы в матчах"""
    
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        
        print("="*70)
        print("⚽ ПРОВЕРКА ГОЛОВ В ПРЕДСКАЗАННЫХ МАТЧАХ")
        print("="*70)
        
        # Ищем предсказания, которые уже могли завершиться
        # (старше 2 часов)
        now = datetime.now()
        old_predictions = []
        
        for pred in predictions:
            ts = pred.get('timestamp', '')
            if ts:
                try:
                    pred_time = datetime.fromisoformat(ts)
                    age = (now - pred_time).total_seconds() / 3600
                    
                    if age > 2:  # старше 2 часов
                        old_predictions.append(pred)
                except:
                    pass
        
        if old_predictions:
            print(f"\n📋 Предсказания, требующие проверки (старше 2 часов): {len(old_predictions)}")
            print("-"*70)
            
            for pred in old_predictions:
                home = pred.get('home_team', '?')
                away = pred.get('away_team', '?')
                minute = pred.get('minute', 0)
                prob = pred.get('goal_probability', 0) * 100
                ts = pred.get('timestamp', '')[:16]
                
                print(f"  {ts} | {minute}' | {home} vs {away} | {prob:.1f}%")
                print("    ❓ Результат неизвестен (нужно обновить was_correct)")
        else:
            print("\n✅ Все предсказания свежие, ждем завершения матчей")
        
        print("\n" + "="*70)
        print("💡 Рекомендация:")
        print("  После завершения матча нужно обновить поле was_correct")
        print("  в predictions.json для учета точности прогнозов")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_goals()