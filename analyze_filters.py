# analyze_filters.py
"""
Скрипт для анализа эффективности фильтров
"""

import json
from collections import defaultdict
from match_analyzer import MatchFilter

def analyze_filter_performance():
    """Анализирует производительность фильтров"""
    
    filter_stats = defaultdict(lambda: {'total': 0, 'goals': 0})
    
    # Загружаем историю матчей
    try:
        with open('data/predictions/predictions.json', 'r') as f:
            data = json.load(f)
            predictions = data.get('predictions', [])
    except:
        print("Нет данных для анализа")
        return
    
    for pred in predictions:
        reason = pred.get('filter_reason', 'unknown')
        had_goal = pred.get('had_goal', False)
        
        filter_stats[reason]['total'] += 1
        if had_goal:
            filter_stats[reason]['goals'] += 1
    
    print("\n" + "="*50)
    print("📊 АНАЛИЗ ЭФФЕКТИВНОСТИ ФИЛЬТРОВ")
    print("="*50)
    
    for reason, stats in sorted(filter_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        if stats['total'] > 0:
            efficiency = stats['goals'] / stats['total']
            print(f"\n{reason}:")
            print(f"  Всего: {stats['total']}")
            print(f"  Голов: {stats['goals']}")
            print(f"  Эффективность: {efficiency:.2%}")

if __name__ == "__main__":
    analyze_filter_performance()