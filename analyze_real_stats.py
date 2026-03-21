# analyze_real_stats.py
"""
Анализ реальной статистики прогнозов и голов
Запуск: python analyze_real_stats.py
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import numpy as np

def analyze_predictions():
    """Анализирует реальные данные из файла predictions.json"""
    
    # Ищем файл с предсказаниями
    paths = [
        'data/predictions/predictions.json',
        'predictions.json',
        'data/predictions.json'
    ]
    
    data = None
    for path in paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Загружен файл: {path}")
            break
    
    if not data:
        print("❌ Файл с предсказаниями не найден")
        return
    
    predictions = data.get('predictions', [])
    accuracy_stats = data.get('accuracy_stats', {})
    
    print(f"\n📊 Всего предсказаний: {len(predictions)}")
    print(f"📊 Статистика точности: {accuracy_stats.get('total_predictions', 0)}")
    
    if not predictions:
        print("❌ Нет данных для анализа")
        return
    
    # Анализируем
    goals_by_minute = defaultdict(int)
    goals_by_period = defaultdict(int)
    predictions_by_minute = defaultdict(int)
    correct_by_minute = defaultdict(int)
    total_by_confidence = defaultdict(int)
    correct_by_confidence = defaultdict(int)
    
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
    
    for pred in predictions:
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0)
        confidence = pred.get('confidence_level', 'MEDIUM')
        was_correct = pred.get('was_correct', False)
        
        # Учитываем только прогнозы с вероятностью выше 45%
        if prob > 0.45:
            predictions_by_minute[minute] += 1
            total_by_confidence[confidence] += 1
            
            if was_correct:
                correct_by_minute[minute] += 1
                correct_by_confidence[confidence] += 1
                
                # Гол состоялся
                goals_by_minute[minute] += 1
                for period_name, (start, end) in periods.items():
                    if start <= minute < end:
                        goals_by_period[period_name] += 1
                        break
    
    # Вывод результатов
    print("\n" + "="*60)
    print("📊 АНАЛИЗ ВРЕМЕНИ ЗАБИТЫХ ГОЛОВ")
    print("="*60)
    
    # 1. Распределение голов по периодам
    print("\n⏱ РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
    print("-"*40)
    
    total_goals = sum(goals_by_period.values())
    
    sorted_periods = sorted(periods.keys(), key=lambda x: periods[x][0])
    for period in sorted_periods:
        count = goals_by_period.get(period, 0)
        percent = (count / total_goals * 100) if total_goals > 0 else 0
        bar = '█' * int(percent / 2)
        print(f"  {period}: {count:3d} голов ({percent:5.1f}%) {bar}")
    
    # 2. Точность прогнозов по минутам
    print("\n🎯 ТОЧНОСТЬ ПРОГНОЗОВ ПО МИНУТАМ:")
    print("-"*40)
    
    minute_accuracy = {}
    for minute in range(0, 95, 5):
        total = 0
        correct = 0
        for m in range(minute, minute+5):
            total += predictions_by_minute.get(m, 0)
            correct += correct_by_minute.get(m, 0)
        
        if total > 5:
            accuracy = correct / total * 100
            minute_accuracy[minute] = accuracy
            bar = '█' * int(accuracy / 5)
            print(f"  {minute}-{minute+4} мин: {total:3d} прогнозов, точность {accuracy:5.1f}% {bar}")
    
    # 3. Самые опасные отрезки
    print("\n🔥 САМЫЕ ОПАСНЫЕ ОТРЕЗКИ (по голам):")
    print("-"*40)
    
    dangerous_periods = sorted(goals_by_period.items(), key=lambda x: x[1], reverse=True)
    for period, count in dangerous_periods:
        percent = (count / total_goals * 100) if total_goals > 0 else 0
        print(f"  {period}: {count} голов ({percent:.1f}%)")
    
    # 4. Оптимальные минуты для прогнозов
    print("\n💡 ОПТИМАЛЬНЫЕ МИНУТЫ ДЛЯ ПРОГНОЗОВ:")
    print("-"*40)
    
    # Находим минуты с высокой точностью и большим количеством голов
    best_minutes = []
    for minute in range(0, 95):
        total = predictions_by_minute.get(minute, 0)
        correct = correct_by_minute.get(minute, 0)
        goals = goals_by_minute.get(minute, 0)
        
        if total > 3 and correct / total > 0.5:
            best_minutes.append((minute, correct/total*100, total, goals))
    
    if best_minutes:
        best_minutes.sort(key=lambda x: x[1], reverse=True)
        for minute, acc, total, goals in best_minutes[:10]:
            print(f"  {minute}' - точность {acc:.1f}% ({total} прогнозов, {goals} голов)")
    
    # 5. Статистика по уверенности
    print("\n📊 СТАТИСТИКА ПО УРОВНЯМ УВЕРЕННОСТИ:")
    print("-"*40)
    
    confidence_order = ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']
    for conf in confidence_order:
        total = total_by_confidence.get(conf, 0)
        correct = correct_by_confidence.get(conf, 0)
        if total > 0:
            acc = correct / total * 100
            bar = '█' * int(acc / 5)
            print(f"  {conf}: {total:3d} прогнозов, точность {acc:5.1f}% {bar}")
    
    # 6. Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ ПО ФИЛЬТРАЦИИ:")
    print("-"*40)
    
    # Находим лучшие и худшие периоды
    best_period = dangerous_periods[0][0] if dangerous_periods else "75-90"
    worst_period = dangerous_periods[-1][0] if dangerous_periods else "0-15"
    
    print(f"  🔴 ЛУЧШЕЕ ВРЕМЯ: {best_period}")
    print(f"  🟢 ХУДШЕЕ ВРЕМЯ: {worst_period}")
    print()
    print("  📌 РЕКОМЕНДАЦИИ:")
    print(f"    • Увеличить вес для минут {best_period} на 20-30%")
    print(f"    • Снизить вес для минут {worst_period} на 30-40%")
    print("    • Исключить сигналы после 85 минуты при разнице в счете >1")
    
    # 7. Общая статистика
    total_pred = sum(predictions_by_minute.values())
    total_correct = sum(correct_by_minute.values())
    overall_accuracy = (total_correct / total_pred * 100) if total_pred > 0 else 0
    
    print("\n📈 ОБЩАЯ СТАТИСТИКА:")
    print("-"*40)
    print(f"  Всего прогнозов (вероятность >45%): {total_pred}")
    print(f"  Из них сбылось: {total_correct}")
    print(f"  Общая точность: {overall_accuracy:.1f}%")
    print(f"  Всего голов: {total_goals}")
    
    print("\n" + "="*60)
    
    return minute_accuracy, goals_by_period, overall_accuracy

def update_match_analyzer(goals_by_period):
    """Обновляет match_analyzer.py на основе статистики"""
    
    # Определяем новые временные факторы на основе статистики
    time_factors = {
        '0-15': 0.5,
        '15-30': 0.7,
        '30-45': 1.0,
        '45-60': 0.8,
        '60-75': 1.1,
        '75-90': 1.3,
        '90+': 0.6
    }
    
    # Обновляем на основе реальных данных
    if goals_by_period:
        total = sum(goals_by_period.values())
        if total > 0:
            for period, count in goals_by_period.items():
                # Нормализуем к среднему значению
                avg = total / len(goals_by_period)
                factor = count / avg
                time_factors[period] = min(1.5, max(0.5, factor))
    
    print("\n📊 НОВЫЕ ВРЕМЕННЫЕ ФАКТОРЫ:")
    for period, factor in time_factors.items():
        print(f"  {period}: {factor:.2f}")
    
    return time_factors

if __name__ == "__main__":
    minute_accuracy, goals_by_period, overall_accuracy = analyze_predictions()
    
    print("\n" + "="*60)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("="*60)
    
    # Сохраняем результаты
    with open('data/stats/goal_time_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({
            'minute_accuracy': minute_accuracy,
            'goals_by_period': goals_by_period,
            'overall_accuracy': overall_accuracy,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Результаты сохранены в data/stats/goal_time_analysis.json")