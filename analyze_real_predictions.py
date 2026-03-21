# analyze_real_predictions.py
"""
Анализ реальных предсказаний из всех источников с правильной фильтрацией
"""

import os
import json
import csv
from datetime import datetime
from collections import defaultdict

def analyze_all_sources():
    """Анализирует все источники предсказаний"""
    
    print("="*60)
    print("📊 АНАЛИЗ ВСЕХ ИСТОЧНИКОВ ПРЕДСКАЗАНИЙ")
    print("="*60)
    
    # 1. Актуальные предсказания из JSON
    print("\n1. АКТУАЛЬНЫЕ ПРЕДСКАЗАНИЯ (JSON):")
    print("-"*40)
    
    json_files = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    json_predictions = []
    for file in json_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                preds = data.get('predictions', [])
                json_predictions.extend(preds)
                print(f"  📄 {file}: {len(preds)} предсказаний")
    
    if json_predictions:
        print(f"\n  📊 Всего в JSON: {len(json_predictions)}")
        for pred in json_predictions:
            prob = pred.get('goal_probability', 0) * 100
            conf = pred.get('confidence_level', 'UNKNOWN')
            minute = pred.get('minute', 0)
            home = pred.get('home_team', 'Unknown')
            away = pred.get('away_team', 'Unknown')
            was_correct = pred.get('was_correct', False)
            status = "✅" if was_correct else "❌"
            print(f"    {status} {home} vs {away} - {prob:.1f}% ({conf}) на {minute}'")
    
    # 2. CSV файлы с историей
    print("\n2. ИСТОРИЧЕСКИЕ ДАННЫЕ (CSV):")
    print("-"*40)
    
    history_dir = 'data/history'
    csv_files = []
    if os.path.exists(history_dir):
        csv_files = [f for f in os.listdir(history_dir) if f.endswith('.csv')]
    
    total_csv_predictions = 0
    csv_predictions = []
    
    for csv_file in csv_files:
        filepath = os.path.join(history_dir, csv_file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Пропускаем первые строки если это не CSV
                content = f.read()
                if ',' in content and '"' in content:
                    # Это CSV файл
                    lines = content.split('\n')
                    count = len([l for l in lines if l.strip() and ',' in l])
                    total_csv_predictions += count
                    print(f"  📄 {csv_file}: ~{count} записей")
        except Exception as e:
            print(f"  ⚠️ {csv_file}: ошибка чтения")
    
    print(f"\n  📊 Всего в CSV: ~{total_csv_predictions} записей")
    
    # 3. База данных
    print("\n3. БАЗА ДАННЫХ:")
    print("-"*40)
    
    db_path = 'data/history/matches_history.db'
    if os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"  Таблицы: {[t[0] for t in tables]}")
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"    • {table[0]}: {count} записей")
        except Exception as e:
            print(f"  Ошибка: {e}")
        
        conn.close()
    else:
        print("  ❌ База данных не найдена")
    
    # 4. Статистика по минутам из JSON
    print("\n4. АНАЛИЗ ВРЕМЕНИ ПРОГНОЗОВ:")
    print("-"*40)
    
    minute_stats = defaultdict(lambda: {'total': 0, 'prob_sum': 0})
    
    for pred in json_predictions:
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0)
        minute_stats[minute]['total'] += 1
        minute_stats[minute]['prob_sum'] += prob
    
    print(f"  Распределение по минутам:")
    for minute in sorted(minute_stats.keys()):
        stats = minute_stats[minute]
        avg_prob = (stats['prob_sum'] / stats['total']) * 100
        print(f"    {minute}' - {stats['total']} прогнозов, средняя вероятность {avg_prob:.1f}%")
    
    # 5. Вывод по периодам
    print("\n5. РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ:")
    print("-"*40)
    
    periods = {
        '0-15': (0, 15),
        '15-30': (15, 30),
        '30-45': (30, 45),
        '45-60': (45, 60),
        '60-75': (60, 75),
        '75-90': (75, 90),
        '90+': (90, 120)
    }
    
    period_stats = defaultdict(lambda: {'total': 0, 'prob_sum': 0})
    
    for pred in json_predictions:
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0)
        for period_name, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period_name]['total'] += 1
                period_stats[period_name]['prob_sum'] += prob
                break
    
    for period_name in periods.keys():
        stats = period_stats[period_name]
        if stats['total'] > 0:
            avg_prob = (stats['prob_sum'] / stats['total']) * 100
            print(f"  {period_name}: {stats['total']} прогнозов, ср.вероятность {avg_prob:.1f}%")
        else:
            print(f"  {period_name}: 0 прогнозов")
    
    # 6. Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("-"*40)
    
    if len(json_predictions) < 10:
        print("  ⚠️ Недостаточно данных для точного анализа (нужно 10+ прогнозов)")
        print("  📌 Запустите бота на несколько дней для накопления статистики")
    
    print("\n  🔧 ДЛЯ УЛУЧШЕНИЯ ТОЧНОСТИ:")
    print("    1. Увеличьте минимальную вероятность сигнала до 50-52%")
    print("    2. Добавьте проверку на was_correct после каждого матча")
    print("    3. Анализируйте только матчи с реальной статистикой")
    print("    4. Исключите матчи без данных об ударах и xG")
    
    print("\n  ⏱ ОПТИМАЛЬНОЕ ВРЕМЯ (на основе мировой статистики):")
    print("    • 75-90 минуты - самое опасное время (30-40% голов)")
    print("    • 30-45 минуты - пик первого тайма (20-25% голов)")
    print("    • 60-75 минуты - середина второго тайма (15-20% голов)")
    print("    • 0-15 минуты - наименее опасное время (5-10% голов)")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    analyze_all_sources()