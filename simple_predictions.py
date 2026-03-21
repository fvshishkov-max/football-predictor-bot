# simple_predictions.py
"""
Простой просмотр предсказаний
"""

import json
import os

pred_file = 'data/predictions/predictions.json'

if os.path.exists(pred_file):
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*60)
    print(f"TOTAL PREDICTIONS: {len(predictions)}")
    print("="*60)
    
    for i, pred in enumerate(predictions[-10:]):
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        ts = pred.get('timestamp', '')[:16]
        
        print(f"{i+1}. {ts} | {minute}' | {home} vs {away} | {prob:.1f}%")
    
    print("="*60)
else:
    print("No predictions file found")