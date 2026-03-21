# final_goal_time_analysis.py
"""
Окончательный анализ оптимального времени для голов на основе исправленных данных
Запуск: python final_goal_time_analysis.py
"""

import json
from collections import defaultdict
import numpy as np

def analyze_goal_time():
    """Анализирует оптимальное время для голов"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*70)
    print("⏱ ОКОНЧАТЕЛЬНЫЙ АНАЛИЗ ОПТИМАЛЬНОГО ВРЕМЕНИ ДЛЯ ГОЛОВ")
    print("="*70)
    
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
    
    # Собираем статистику
    period_stats = defaultdict(lambda: {'total': 0, 'goals': 0, 'prob_sum': 0})
    minute_stats = defaultdict(lambda: {'total': 0, 'goals': 0, 'prob_sum': 0})
    
    for pred in predictions:
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0)
        was_correct = pred.get('was_correct', False)
        
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period_name]['total'] += 1
                period_stats[period_name]['prob_sum'] += prob
                if was_correct:
                    period_stats[period_name]['goals'] += 1
                break
        
        minute_stats[minute]['total'] += 1
        minute_stats[minute]['prob_sum'] += prob
        if was_correct:
            minute_stats[minute]['goals'] += 1
    
    # 1. ОБЩАЯ СТАТИСТИКА
    total_goals = sum(p['goals'] for p in period_stats.values())
    total_predictions = len(predictions)
    
    print("\n📊 ОБЩАЯ СТАТИСТИКА:")
    print("-"*50)
    print(f"  • Всего прогнозов: {total_predictions}")
    print(f"  • Всего голов: {total_goals}")
    print(f"  • Общая точность: {total_goals/total_predictions*100:.2f}%")
    
    # 2. РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ
    print("\n📊 РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
    print("-"*50)
    print(f"{'Период':<10} {'Прогнозы':<10} {'Голы':<8} {'Вероятность':<12} {'Точность':<10} График")
    print("-"*50)
    
    for period_name in periods.keys():
        stats = period_stats[period_name]
        total = stats['total']
        goals = stats['goals']
        avg_prob = (stats['prob_sum'] / total * 100) if total > 0 else 0
        accuracy = (goals / total * 100) if total > 0 else 0
        
        bar = '█' * int(accuracy / 2)
        print(f"{period_name:<10} {total:<10} {goals:<8} {avg_prob:<12.1f}% {accuracy:<10.1f}% {bar}")
    
    # 3. САМЫЕ ОПАСНЫЕ ПЕРИОДЫ (по количеству голов)
    print("\n🔥 САМЫЕ ОПАСНЫЕ ПЕРИОДЫ (по количеству голов):")
    print("-"*50)
    
    sorted_by_goals = sorted(period_stats.items(), key=lambda x: x[1]['goals'], reverse=True)
    for period_name, stats in sorted_by_goals:
        goals = stats['goals']
        total = stats['total']
        accuracy = (goals / total * 100) if total > 0 else 0
        bar = '█' * int(accuracy / 2)
        print(f"  {period_name}: {goals:4d} голов из {total:5d} прогнозов ({accuracy:5.1f}%) {bar}")
    
    # 4. ЛУЧШАЯ ТОЧНОСТЬ ПО ПЕРИОДАМ
    print("\n🎯 ЛУЧШАЯ ТОЧНОСТЬ ПО ПЕРИОДАМ:")
    print("-"*50)
    
    sorted_by_accuracy = sorted(period_stats.items(), key=lambda x: x[1]['goals']/x[1]['total'] if x[1]['total'] > 0 else 0, reverse=True)
    for period_name, stats in sorted_by_accuracy[:3]:
        goals = stats['goals']
        total = stats['total']
        accuracy = (goals / total * 100) if total > 0 else 0
        print(f"  🥇 {period_name}: {accuracy:.1f}% ({goals}/{total})")
    
    # 5. ТОП-10 МИНУТ ПО ТОЧНОСТИ
    print("\n⏱ ТОП-10 МИНУТ ПО ТОЧНОСТИ (минимум 5 прогнозов):")
    print("-"*50)
    
    minute_accuracy = []
    for minute in range(0, 95):
        stats = minute_stats[minute]
        if stats['total'] >= 5:
            accuracy = (stats['goals'] / stats['total'] * 100) if stats['total'] > 0 else 0
            minute_accuracy.append((minute, accuracy, stats['total'], stats['goals']))
    
    minute_accuracy.sort(key=lambda x: x[1], reverse=True)
    for minute, acc, total, goals in minute_accuracy[:10]:
        print(f"  {minute:2d}' - {acc:5.1f}% ({goals}/{total})")
    
    # 6. ТОП-10 МИНУТ ПО КОЛИЧЕСТВУ ГОЛОВ
    print("\n⚽ ТОП-10 МИНУТ ПО КОЛИЧЕСТВУ ГОЛОВ:")
    print("-"*50)
    
    minute_goals = [(minute, stats['goals'], stats['total']) 
                    for minute, stats in minute_stats.items() 
                    if stats['goals'] > 0]
    minute_goals.sort(key=lambda x: x[1], reverse=True)
    for minute, goals, total in minute_goals[:10]:
        print(f"  {minute:2d}' - {goals} голов (всего прогнозов: {total})")
    
    # 7. РЕКОМЕНДАЦИИ
    print("\n💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
    print("-"*50)
    
    # Находим лучший период
    best_period = sorted_by_accuracy[0][0]
    best_accuracy = (period_stats[best_period]['goals'] / period_stats[best_period]['total'] * 100)
    
    # Находим худший период
    worst_period = sorted_by_accuracy[-1][0]
    worst_accuracy = (period_stats[worst_period]['goals'] / period_stats[worst_period]['total'] * 100)
    
    print(f"\n  🔴 ЛУЧШЕЕ ВРЕМЯ: {best_period} (точность {best_accuracy:.1f}%)")
    print(f"  🟢 ХУДШЕЕ ВРЕМЯ: {worst_period} (точность {worst_accuracy:.1f}%)")
    
    print("\n  📌 КЛЮЧЕВЫЕ РЕКОМЕНДАЦИИ:")
    print(f"    1. Увеличить вес для периода {best_period} на 30-50%")
    print(f"    2. Снизить вес для периода {worst_period} на 30-40%")
    print("    3. Оптимальные минуты для сигналов:")
    
    # Топ-5 минут по точности
    for minute, acc, total, goals in minute_accuracy[:5]:
        print(f"       • {minute}' - точность {acc:.1f}%")
    
    print("\n    4. Минуты, которые стоит исключить:")
    worst_minutes = minute_accuracy[-5:] if len(minute_accuracy) >= 5 else []
    for minute, acc, total, goals in worst_minutes:
        print(f"       • {minute}' - точность {acc:.1f}%")
    
    # 8. ВЕСА ДЛЯ MATCH_ANALYZER
    print("\n📊 РЕКОМЕНДУЕМЫЕ ВЕСА ДЛЯ MATCH_ANALYZER:")
    print("-"*50)
    
    # Вычисляем веса на основе точности
    total_accuracy = sum((stats['goals'] / stats['total'] * 100) if stats['total'] > 0 else 0 
                         for stats in period_stats.values())
    
    weights = {}
    for period_name, stats in period_stats.items():
        accuracy = (stats['goals'] / stats['total'] * 100) if stats['total'] > 0 else 0
        if total_accuracy > 0:
            weight = accuracy / total_accuracy * len(periods) * 0.8
        else:
            weight = 1.0
        weights[period_name] = round(max(0.5, min(1.5, weight)), 2)
    
    print("\n  time_factors = {")
    for period_name, weight in weights.items():
        print(f"      '{period_name}': {weight},")
    print("  }")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    analyze_goal_time()