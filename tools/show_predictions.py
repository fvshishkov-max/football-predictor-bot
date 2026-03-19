"""
Показывает последние предсказания
"""

import json
import os

def show_predictions(limit=20):
    """Показывает последние предсказания"""
    
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in paths_to_try:
        if os.path.exists(path):
            found_file = path
            break
    
    if not found_file:
        print("❌ Файл с предсказаниями не найден!")
        return
    
    print(f"\n📋 ПОСЛЕДНИЕ {limit} ПРЕДСКАЗАНИЙ")
    print("="*80)
    
    with open(found_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    if not predictions:
        print("❌ Нет предсказаний")
        return
    
    for pred in predictions[-limit:]:
        ts = pred.get('timestamp', '')
        home = pred.get('home_team', 'Unknown')
        away = pred.get('away_team', 'Unknown')
        prob = pred.get('goal_probability', 0) * 100
        conf = pred.get('confidence_level', 'UNKNOWN')
        signal = "✅" if pred.get('signal') else "❌"
        
        correct = pred.get('was_correct', '?')
        if correct is not True and correct is not False:
            correct_mark = "❓"
        else:
            correct_mark = "✅" if correct else "❌"
        
        print(f"{ts[:19]} | {correct_mark} | {signal} | {home:20} vs {away:20} | {prob:5.1f}% | {conf}")

if __name__ == "__main__":
    show_predictions()
