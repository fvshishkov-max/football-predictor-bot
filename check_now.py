# check_now.py
"""
Быстрая проверка текущего состояния
Запуск: python check_now.py
"""

import json
import os
from datetime import datetime

print("="*60)
print(f"CURRENT STATUS - {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

# Предсказания
if os.path.exists('data/predictions/predictions.json'):
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        preds = data.get('predictions', [])
        print(f"\nPredictions: {len(preds)}")
        
        if preds:
            last = preds[-1]
            print(f"Last: {last.get('timestamp', '')[:16]} - {last.get('home_team')} vs {last.get('away_team')}")
            print(f"Probability: {last.get('goal_probability', 0)*100:.1f}%")
            
            # Считаем сигналы
            signals = [p for p in preds if p.get('goal_probability', 0) > 0.46]
            print(f"Signals (>46%): {len(signals)}")
            if signals:
                last_signal = signals[-1]
                print(f"Last signal: {last_signal.get('timestamp', '')[:16]} - {last_signal.get('home_team')} vs {last_signal.get('away_team')} ({last_signal.get('goal_probability', 0)*100:.1f}%)")

# Логи
if os.path.exists('data/logs/app.log'):
    with open('data/logs/app.log', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print(f"\nLog lines: {len(lines)}")
        if lines:
            print(f"Last log: {lines[-1].strip()[:100]}")

print("\n" + "="*60)