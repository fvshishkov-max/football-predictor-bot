"""
Статистика за определенную дату
Запуск: python tools/stats_by_date.py YYYY-MM-DD
"""

import sys
import json
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_predictions():
    """Загружает историю предсказаний"""
    files_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    for file_path in files_to_try:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                continue
    return None

def get_stats_by_date(date_str):
    """Получает статистику за указанную дату"""
    
    data = load_predictions()
    if not data:
        return None
    
    predictions = data.get('predictions', [])
    
    date_stats = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'matches': []
    }
    
    for pred in predictions:
        timestamp = pred.get('timestamp', '')
        if timestamp[:10] == date_str:
            was_correct = pred.get('was_correct', False)
            date_stats['total'] += 1
            if was_correct:
                date_stats['correct'] += 1
            else:
                date_stats['incorrect'] += 1
            
            date_stats['matches'].append({
                'home': pred.get('home_team', 'Unknown'),
                'away': pred.get('away_team', 'Unknown'),
                'prob': pred.get('goal_probability', 0) * 100,
                'correct': was_correct
            })
    
    if date_stats['total'] > 0:
        date_stats['accuracy'] = (date_stats['correct'] / date_stats['total']) * 100
    else:
        date_stats['accuracy'] = 0
    
    return date_stats

def main():
    if len(sys.argv) < 2:
        print("❌ Укажите дату в формате ГГГГ-ММ-ДД")
        print("Пример: python tools/stats_by_date.py 2026-03-19")
        return
    
    date_str = sys.argv[1]
    
    print(f"\n📊 СТАТИСТИКА ЗА {date_str}")
    print("="*50)
    
    stats = get_stats_by_date(date_str)
    
    if not stats or stats['total'] == 0:
        print(f"❌ Нет прогнозов за {date_str}")
        return
    
    print(f"📈 Всего прогнозов: {stats['total']}")
    print(f"✅ Совпало: {stats['correct']}")
    print(f"❌ Не совпало: {stats['incorrect']}")
    print(f"🎯 Точность: {stats['accuracy']:.1f}%")
    
    if stats['matches']:
        print("\n📋 Матчи:")
        for match in stats['matches']:
            mark = "✅" if match['correct'] else "❌"
            print(f"  {mark} {match['home']} vs {match['away']} - {match['prob']:.1f}%")

if __name__ == "__main__":
    main()
