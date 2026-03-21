# analyze_goal_events.py
"""
Анализ событий голов из истории
Запуск: python analyze_goal_events.py
"""

import json
from collections import defaultdict
import matplotlib.pyplot as plt

def analyze_goal_events():
    """Анализирует события голов"""
    
    # Загружаем данные
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    # Собираем только события, где был гол
    goal_events = [p for p in predictions if p.get('was_correct', False)]
    
    print("="*60)
    print("⚽ АНАЛИЗ СОБЫТИЙ ГОЛОВ")
    print("="*60)
    print(f"\n📊 Всего голов в истории: {len(goal_events)}")
    
    if not goal_events:
        print("❌ Нет данных о голах")
        return
    
    # Статистика по минутам
    minute_stats = defaultdict(int)
    for event in goal_events:
        minute = event.get('minute', 0)
        minute_stats[minute] += 1
    
    # Периоды
    periods = {
        'Начало (0-15)': (0, 15),
        'Разогрев (15-30)': (15, 30),
        'Пик 1-го тайма (30-45)': (30, 45),
        'После перерыва (45-60)': (45, 60),
        'Середина 2-го (60-75)': (60, 75),
        'Концовка (75-90)': (75, 90),
        'Добавленное (90+)': (90, 120)
    }
    
    period_stats = defaultdict(int)
    for minute, count in minute_stats.items():
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period_name] += count
                break
    
    total = sum(period_stats.values())
    
    print("\n📊 РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
    print("-"*50)
    
    for period_name in periods.keys():
        count = period_stats.get(period_name, 0)
        percent = (count / total * 100) if total > 0 else 0
        bar = '█' * int(percent / 2)
        print(f"  {period_name:<20}: {count:4d} голов ({percent:5.1f}%) {bar}")
    
    print("\n🔥 САМЫЕ ОПАСНЫЕ МИНУТЫ:")
    print("-"*50)
    
    top_minutes = sorted(minute_stats.items(), key=lambda x: x[1], reverse=True)[:15]
    for minute, count in top_minutes:
        percent = (count / total * 100) if total > 0 else 0
        bar = '█' * int(percent / 2)
        print(f"  {minute:2d}' - {count:3d} голов ({percent:5.1f}%) {bar}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    analyze_goal_events()