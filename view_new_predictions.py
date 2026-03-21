# view_new_predictions.py
"""
Просмотр новых предсказаний
Запуск: python view_new_predictions.py
"""

import json
import time
from datetime import datetime, timedelta

def view_new():
    """Показывает предсказания за последний час"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    now = datetime.now()
    
    # Фильтруем за последний час
    recent = []
    for pred in predictions:
        ts = pred.get('timestamp', '')
        if ts:
            try:
                pred_time = datetime.fromisoformat(ts)
                if (now - pred_time).total_seconds() < 3600:
                    recent.append(pred)
            except:
                pass
    
    print("="*70)
    print(f"NEW PREDICTIONS (last hour) - Total: {len(recent)}")
    print("="*70)
    
    for pred in recent[-10:]:
        ts = pred.get('timestamp', '')[:16]
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        conf = pred.get('confidence_level', '?')
        
        print(f"{ts} | {minute:2d}' | {home:25} vs {away:25} | {prob:5.1f}% | {conf}")
    
    print("="*70)
    print(f"Total predictions in file: {len(predictions)}")
    print("="*70)

if __name__ == "__main__":
    view_new()