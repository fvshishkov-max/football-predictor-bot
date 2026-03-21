# analyze_goal_times_from_history.py
"""
Анализ времени забитых голов из истории матчей
Запуск: python analyze_goal_times_from_history.py
"""

import sqlite3
import os
from collections import defaultdict
from datetime import datetime

def analyze_goals_from_db():
    """Анализирует голы из базы данных истории матчей"""
    
    db_path = 'data/history/matches_history.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    print("="*60)
    print("⏱ АНАЛИЗ ВРЕМЕНИ ГОЛОВ ИЗ ИСТОРИИ МАТЧЕЙ")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем структуру таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n📊 Таблицы: {[t[0] for t in tables]}")
    
    # Ищем данные о голах
    goals_by_minute = defaultdict(int)
    total_matches = 0
    total_goals = 0
    
    # Пытаемся получить данные из разных таблиц
    try:
        # Если есть таблица matches с данными о голах
        cursor.execute("SELECT home_score, away_score FROM matches")
        matches = cursor.fetchall()
        total_matches = len(matches)
        for home, away in matches:
            total_goals += (home or 0) + (away or 0)
        print(f"\n📊 Статистика матчей:")
        print(f"  Всего матчей: {total_matches}")
        print(f"  Всего голов: {total_goals}")
        print(f"  Средняя результативность: {total_goals/total_matches:.2f} гола за матч")
    except:
        print("  Нет данных о счетах")
    
    # Если есть таблица с минутами голов
    try:
        cursor.execute("SELECT minute, count FROM goals_by_minute")
        goals = cursor.fetchall()
        for minute, count in goals:
            goals_by_minute[minute] = count
        print(f"\n⏱ Распределение голов по минутам:")
        for minute in sorted(goals_by_minute.keys()):
            print(f"  {minute}' - {goals_by_minute[minute]} голов")
    except:
        print("  Нет данных о минутах голов")
    
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
    
    period_goals = defaultdict(int)
    
    # Если есть данные о минутах
    if goals_by_minute:
        for minute, count in goals_by_minute.items():
            for period_name, (start, end) in periods.items():
                if start <= minute < end:
                    period_goals[period_name] += count
                    break
        
        print(f"\n📊 РАСПРЕДЕЛЕНИЕ ГОЛОВ ПО ПЕРИОДАМ:")
        print("-"*40)
        total = sum(period_goals.values())
        for period in periods.keys():
            count = period_goals.get(period, 0)
            percent = (count / total * 100) if total > 0 else 0
            bar = '█' * int(percent / 2)
            print(f"  {period}: {count:3d} голов ({percent:5.1f}%) {bar}")
        
        # Самые опасные отрезки
        print(f"\n🔥 САМЫЕ ОПАСНЫЕ ОТРЕЗКИ:")
        sorted_periods = sorted(period_goals.items(), key=lambda x: x[1], reverse=True)
        for period, count in sorted_periods[:3]:
            percent = (count / total * 100) if total > 0 else 0
            print(f"  {period}: {count} голов ({percent:.1f}%)")
    
    # Статистика по матчам
    print(f"\n📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("-"*40)
    print(f"  Всего матчей в истории: {total_matches}")
    print(f"  Всего голов: {total_goals}")
    print(f"  Средняя результативность: {total_goals/total_matches:.2f}" if total_matches > 0 else "Нет данных")
    
    conn.close()
    
    print("\n" + "="*60)
    
    return period_goals, goals_by_minute

if __name__ == "__main__":
    analyze_goals_from_db()