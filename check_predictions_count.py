# check_predictions_count.py
"""
Проверка количества новых предсказаний
Запуск: python check_predictions_count.py
"""

import json
import time
from datetime import datetime, timedelta

def check():
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    now = datetime.now()
    
    # Предсказания за последний час
    last_hour = 0
    for pred in predictions:
        ts = pred.get('timestamp', '')
        if ts:
            try:
                pred_time = datetime.fromisoformat(ts)
                if (now - pred_time).total_seconds() < 3600:
                    last_hour += 1
            except:
                pass
    
    print("="*60)
    print("PREDICTIONS STATUS")
    print("="*60)
    print(f"Total predictions: {len(predictions)}")
    print(f"Last hour: {last_hour}")
    print(f"Last 10 minutes: ", end="")
    
    # Предсказания за последние 10 минут
    last_10min = 0
    for pred in predictions:
        ts = pred.get('timestamp', '')
        if ts:
            try:
                pred_time = datetime.fromisoformat(ts)
                if (now - pred_time).total_seconds() < 600:
                    last_10min += 1
            except:
                pass
    print(last_10min)
    
    print("="*60)

if __name__ == "__main__":
    check()