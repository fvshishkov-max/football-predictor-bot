# analyze_goal_time.py
"""
Анализ оптимального времени для голов из импортированных данных
Запуск: python analyze_goal_time.py
"""

import json
from collections import defaultdict

def analyze_goal_time():
    """Анализирует время голов из predictions.json"""
    
    # Загружаем данные
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*60)
    print("⏱ АНАЛИЗ ОПТИМАЛЬНОГО ВРЕМЕНИ ДЛЯ ГОЛОВ")
    print("="*60)
    
    # Периоды
    periods = {
        '0-15': (0, 15),
        '15-30': (15, 30),
        '30-45': (30, 45),
        '45-60': (45, 60),
        '60-75': (60, 75),
        '75-90': (75, 90),
        '90+': (90, 120)
    }
    
    # Собираем статистику по минутам
    minute_stats = defaultdict(lambda: {'total': 0, 'goals': 0, 'correct': 0})
    period_stats = defaultdict(lambda: {'total': 0, 'goals': 0, 'correct': 0})
    
    for pred in predictions:
        minute = pred.get('minute', 0)
        was_correct = pred.get('was_correct', False)
        prob = pred.get('goal_probability', 0)
        
        minute_stats[minute]['total'] += 1
        if was_correct:
            minute_stats[minute]['goals'] += 1
            minute_stats[minute]['correct'] += 1
        
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period_name]['total'] += 1
                if was_correct:
                    period_stats[period_name]['goals'] += 1
                    period_stats[period_name]['correct'] += 1
                break
    
    # Выводим результаты по периодам
    print("\n📊 РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
    print("-"*50)
    
    total_goals = sum(p['goals'] for p in period_stats.values())
    
    for period_name in periods.keys():
        stats = period_stats[period_name]
        total = stats['total']
        goals = stats['goals']
        
        if total > 0:
            goal_rate = (goals / total * 100) if total > 0 else 0
            bar = '█' * int(goal_rate / 2)
            print(f"  {period_name}: {goals:4d} голов из {total:5d} прогнозов ({goal_rate:5.1f}%) {bar}")
        else:
            print(f"  {period_name}: 0 голов из 0 прогнозов (0.0%)")
    
    # Находим лучший период
    best_period = None
    best_rate = 0
    for period_name, stats in period_stats.items():
        if stats['total'] > 50:
            rate = stats['goals'] / stats['total'] * 100
            if rate > best_rate:
                best_rate = rate
                best_period = period_name
    
    # Находим худший период
    worst_period = None
    worst_rate = 100
    for period_name, stats in period_stats.items():
        if stats['total'] > 50:
            rate = stats['goals'] / stats['total'] * 100
            if rate < worst_rate:
                worst_rate = rate
                worst_period = period_name
    
    print("\n🔥 САМЫЕ ОПАСНЫЕ ПЕРИОДЫ:")
    print("-"*50)
    
    # Сортируем по количеству голов
    sorted_periods = sorted(period_stats.items(), key=lambda x: x[1]['goals'], reverse=True)
    for period_name, stats in sorted_periods[:3]:
        goal_rate = (stats['goals'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {period_name}: {stats['goals']} голов, {stats['total']} прогнозов ({goal_rate:.1f}%)")
    
    print("\n💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
    print("-"*50)
    
    if best_period:
        print(f"  🔴 УВЕЛИЧИТЬ ВЕС ДЛЯ {best_period} (точность {best_rate:.1f}%)")
    if worst_period:
        print(f"  🟢 СНИЗИТЬ ВЕС ДЛЯ {worst_period} (точность {worst_rate:.1f}%)")
    
    print(f"\n  📌 КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print(f"     • Всего проанализировано прогнозов: {len(predictions)}")
    print(f"     • Из них голов: {total_goals}")
    print(f"     • Общая точность: {total_goals/len(predictions)*100:.1f}%")
    
    # Анализ по минутам (самые точные минуты)
    print("\n🎯 САМЫЕ ТОЧНЫЕ МИНУТЫ (>= 3 прогнозов):")
    print("-"*50)
    
    accurate_minutes = []
    for minute, stats in minute_stats.items():
        if stats['total'] >= 3:
            accuracy = stats['goals'] / stats['total'] * 100
            accurate_minutes.append((minute, accuracy, stats['total'], stats['goals']))
    
    accurate_minutes.sort(key=lambda x: x[1], reverse=True)
    for minute, acc, total, goals in accurate_minutes[:10]:
        print(f"  {minute}' - {acc:.1f}% ({goals}/{total})")
    
    print("\n" + "="*60)
    
    return period_stats, minute_stats

if __name__ == "__main__":
    analyze_goal_time()