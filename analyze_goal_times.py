# analyze_goal_times.py
"""
Анализ времени забитых голов из истории матчей
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def analyze_goal_times():
    """Анализирует время забитых голов из истории"""
    
    # Пробуем загрузить предсказания
    predictions_file = 'data/predictions/predictions.json'
    if not os.path.exists(predictions_file):
        print("❌ Нет данных для анализа. Запустите бота на несколько дней.")
        return
    
    with open(predictions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    if not predictions:
        print("❌ Нет предсказаний в файле")
        return
    
    # Анализируем
    goals_by_minute = defaultdict(int)
    goals_by_period = defaultdict(int)
    total_predictions = 0
    correct_predictions = 0
    
    periods = {
        '0-15': (0, 15),
        '15-30': (15, 30),
        '30-45': (30, 45),
        '45-60': (45, 60),
        '60-75': (60, 75),
        '75-90': (75, 90),
        '90+': (90, 120)
    }
    
    for pred in predictions:
        if 'goal_probability' not in pred:
            continue
        
        total_predictions += 1
        
        minute = pred.get('minute', 0)
        goal_occurred = pred.get('was_correct', False)
        
        if goal_occurred:
            correct_predictions += 1
            goals_by_minute[minute] += 1
            
            # По периодам
            for period_name, (start, end) in periods.items():
                if start <= minute < end:
                    goals_by_period[period_name] += 1
                    break
    
    # Вывод результатов
    print("="*60)
    print("📊 АНАЛИЗ ВРЕМЕНИ ЗАБИТЫХ ГОЛОВ")
    print("="*60)
    print()
    print(f"📈 Всего предсказаний: {total_predictions}")
    print(f"✅ Сбылось: {correct_predictions}")
    print(f"🎯 Точность: {correct_predictions/total_predictions*100:.1f}%" if total_predictions > 0 else "Нет данных")
    print()
    
    if goals_by_period:
        print("⏱ РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
        print("-"*40)
        for period_name, count in sorted(goals_by_period.items()):
            percent = (count / correct_predictions * 100) if correct_predictions > 0 else 0
            bar = '█' * int(percent / 2)
            print(f"  {period_name}: {count} голов ({percent:.1f}%) {bar}")
    
    print()
    print("📊 РЕКОМЕНДАЦИИ ПО ФИЛЬТРАЦИИ:")
    print("-"*40)
    
    # Оптимальные периоды для сигналов
    high_prob_periods = ['75-90', '15-30', '30-45']
    medium_prob_periods = ['60-75', '45-60']
    low_prob_periods = ['0-15', '90+']
    
    print(f"  🔴 ЛУЧШЕЕ ВРЕМЯ: {', '.join(high_prob_periods)}")
    print(f"  🟡 СРЕДНЕЕ ВРЕМЯ: {', '.join(medium_prob_periods)}")
    print(f"  🟢 ХУДШЕЕ ВРЕМЯ: {', '.join(low_prob_periods)}")
    print()
    print("💡 РЕКОМЕНДАЦИИ:")
    print("  • Увеличить порог вероятности для минут 0-15 и 90+")
    print("  • Повысить приоритет для минут 75-90")
    print("  • Исключить сигналы после 85 минуты при разнице в счете >1")
    
    print("="*60)
    
    return goals_by_minute, goals_by_period

if __name__ == "__main__":
    analyze_goal_times()