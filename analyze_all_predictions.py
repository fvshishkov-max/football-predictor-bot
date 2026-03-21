# analyze_all_predictions.py
"""
Полный анализ всех предсказаний из всех источников
Запуск: python analyze_all_predictions.py
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import numpy as np

def analyze_all_predictions():
    """Анализирует все предсказания из всех файлов"""
    
    print("="*60)
    print("📊 ПОЛНЫЙ АНАЛИЗ ПРЕДСКАЗАНИЙ")
    print("="*60)
    
    # Загружаем все предсказания
    all_predictions = []
    
    # 1. Из data/predictions/predictions.json
    file1 = 'data/predictions/predictions.json'
    if os.path.exists(file1):
        with open(file1, 'r', encoding='utf-8') as f:
            data = json.load(f)
            preds = data.get('predictions', [])
            all_predictions.extend(preds)
            print(f"✅ Загружено из {file1}: {len(preds)} предсказаний")
    
    # 2. Из data/predictions.json
    file2 = 'data/predictions.json'
    if os.path.exists(file2):
        with open(file2, 'r', encoding='utf-8') as f:
            data = json.load(f)
            preds = data.get('predictions', [])
            all_predictions.extend(preds)
            print(f"✅ Загружено из {file2}: {len(preds)} предсказаний")
    
    print(f"\n📊 Всего предсказаний: {len(all_predictions)}")
    
    # Фильтруем уникальные по match_id и timestamp
    unique_predictions = {}
    for pred in all_predictions:
        key = f"{pred.get('match_id')}_{pred.get('timestamp', '')[:19]}"
        if key not in unique_predictions:
            unique_predictions[key] = pred
    
    print(f"📊 Уникальных предсказаний: {len(unique_predictions)}")
    
    # Анализ
    predictions = list(unique_predictions.values())
    
    # Статистика по датам
    print("\n📅 РАСПРЕДЕЛЕНИЕ ПО ДАТАМ:")
    print("-"*40)
    dates = defaultdict(int)
    for pred in predictions:
        ts = pred.get('timestamp', '')
        if ts:
            date = ts[:10] if len(ts) > 10 else ts
            dates[date] += 1
    
    for date, count in sorted(dates.items()):
        print(f"  {date}: {count} предсказаний")
    
    # Статистика по уверенности
    print("\n🎯 СТАТИСТИКА ПО УРОВНЯМ УВЕРЕННОСТИ:")
    print("-"*40)
    conf_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for pred in predictions:
        conf = pred.get('confidence_level', 'UNKNOWN')
        was_correct = pred.get('was_correct', False)
        conf_stats[conf]['total'] += 1
        if was_correct:
            conf_stats[conf]['correct'] += 1
    
    for conf in ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW', 'UNKNOWN']:
        if conf in conf_stats:
            total = conf_stats[conf]['total']
            correct = conf_stats[conf]['correct']
            acc = (correct / total * 100) if total > 0 else 0
            bar = '█' * int(acc / 2)
            print(f"  {conf}: {total:5d} прогнозов, точность {acc:5.1f}% {bar}")
    
    # Статистика по минутам
    print("\n⏱ ТОЧНОСТЬ ПО МИНУТАМ:")
    print("-"*40)
    
    minute_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    for pred in predictions:
        minute = pred.get('minute', 0)
        was_correct = pred.get('was_correct', False)
        minute_stats[minute]['total'] += 1
        if was_correct:
            minute_stats[minute]['correct'] += 1
    
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
    
    period_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'goals': 0})
    
    for minute in range(0, 95):
        total = minute_stats[minute]['total']
        correct = minute_stats[minute]['correct']
        
        if total > 0:
            for period_name, (start, end) in periods.items():
                if start <= minute < end:
                    period_stats[period_name]['total'] += total
                    period_stats[period_name]['correct'] += correct
                    break
    
    print("\n📊 РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ:")
    for period_name in periods.keys():
        total = period_stats[period_name]['total']
        correct = period_stats[period_name]['correct']
        if total > 0:
            acc = (correct / total * 100)
            bar = '█' * int(acc / 2)
            print(f"  {period_name}: {total:5d} прогнозов, точность {acc:5.1f}% {bar}")
    
    # Оптимальные минуты
    print("\n💡 ОПТИМАЛЬНЫЕ МИНУТЫ ДЛЯ ПРОГНОЗОВ:")
    print("-"*40)
    
    best_minutes = []
    for minute in range(0, 95):
        total = minute_stats[minute]['total']
        correct = minute_stats[minute]['correct']
        if total > 5:
            acc = correct / total * 100
            if acc > 50:  # Только где точность выше 50%
                best_minutes.append((minute, acc, total))
    
    if best_minutes:
        best_minutes.sort(key=lambda x: x[1], reverse=True)
        for minute, acc, total in best_minutes[:10]:
            print(f"  {minute}' - точность {acc:.1f}% ({total} прогнозов)")
    else:
        print("  Нет минут с точностью выше 50%")
    
    # Самые опасные отрезки (по количеству голов)
    print("\n🔥 САМЫЕ ОПАСНЫЕ ОТРЕЗКИ (по количеству голов):")
    print("-"*40)
    
    # Вычисляем где было больше всего голов
    goal_minutes = defaultdict(int)
    for pred in predictions:
        if pred.get('was_correct', False):
            minute = pred.get('minute', 0)
            goal_minutes[minute] += 1
    
    period_goals = defaultdict(int)
    for minute, count in goal_minutes.items():
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_goals[period_name] += count
                break
    
    if period_goals:
        sorted_periods = sorted(period_goals.items(), key=lambda x: x[1], reverse=True)
        for period, count in sorted_periods:
            print(f"  {period}: {count} голов")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
    print("-"*40)
    
    total_correct = sum(conf_stats[conf]['correct'] for conf in conf_stats)
    total_predictions = sum(conf_stats[conf]['total'] for conf in conf_stats)
    overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
    
    print(f"  • Общая точность: {overall_accuracy:.1f}%")
    
    if overall_accuracy < 10:
        print("  • 🔴 КРИТИЧЕСКИ НИЗКАЯ ТОЧНОСТЬ!")
        print("  • Необходимо срочно улучшить алгоритм отбора сигналов")
        print("  • Увеличить минимальный порог вероятности до 50-55%")
        print("  • Исключить прогнозы с уровнем UNKNOWN")
    
    # Находим лучший период
    best_period = None
    best_acc = 0
    for period_name in periods.keys():
        total = period_stats[period_name]['total']
        correct = period_stats[period_name]['correct']
        if total > 50:
            acc = correct / total * 100
            if acc > best_acc:
                best_acc = acc
                best_period = period_name
    
    if best_period:
        print(f"  • Лучшее время для прогнозов: {best_period} (точность {best_acc:.1f}%)")
    
    print("\n" + "="*60)
    
    return period_stats, period_goals, overall_accuracy

if __name__ == "__main__":
    analyze_all_predictions()