# analyze_with_results.py
"""
Анализ предсказаний с учетом реальных результатов
Запуск: python analyze_with_results.py
"""

import json
from collections import defaultdict

def analyze():
    """Анализирует предсказания с результатами"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*70)
    print("📊 АНАЛИЗ ПРЕДСКАЗАНИЙ С РЕЗУЛЬТАТАМИ")
    print("="*70)
    
    # Статистика по периодам
    periods = {
        '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
        '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
        '90+': (90, 120)
    }
    
    period_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'goals': 0})
    
    for pred in predictions:
        minute = pred.get('minute', 0)
        was_correct = pred.get('was_correct', False)
        home_score = pred.get('home_score', 0)
        away_score = pred.get('away_score', 0)
        total_goals = home_score + away_score
        
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period_name]['total'] += 1
                if was_correct:
                    period_stats[period_name]['correct'] += 1
                period_stats[period_name]['goals'] += total_goals
                break
    
    print("\n📊 РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ:")
    print("-"*70)
    print(f"{'Период':<10} {'Прогнозы':<10} {'Сбылось':<10} {'Точность':<12} {'Голов':<8}")
    print("-"*70)
    
    for period_name in periods.keys():
        stats = period_stats[period_name]
        total = stats['total']
        correct = stats['correct']
        accuracy = (correct / total * 100) if total > 0 else 0
        goals = stats['goals']
        
        if total > 0:
            bar = '█' * int(accuracy / 5)
            print(f"{period_name:<10} {total:<10} {correct:<10} {accuracy:<11.1f}% {goals:<8} {bar}")
    
    # Общая статистика
    total = len(predictions)
    correct = sum(1 for p in predictions if p.get('was_correct', False))
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print("\n📈 ОБЩАЯ СТАТИСТИКА:")
    print("-"*70)
    print(f"  Всего предсказаний: {total}")
    print(f"  Сбылось: {correct}")
    print(f"  Точность: {accuracy:.1f}%")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("-"*70)
    
    # Находим лучший период
    best_period = None
    best_acc = 0
    for period, stats in period_stats.items():
        if stats['total'] > 3:
            acc = stats['correct'] / stats['total'] * 100
            if acc > best_acc:
                best_acc = acc
                best_period = period
    
    if best_period:
        print(f"  🔴 Лучшее время для сигналов: {best_period} (точность {best_acc:.1f}%)")
    
    print("\n  📌 Для улучшения точности:")
    print("    1. Увеличить порог вероятности до 45-48%")
    print("    2. Исключить периоды с низкой точностью")
    print("    3. Добавить больше факторов (форма команд, xG)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    analyze()