# analyze_history.py
"""
Анализ истории предсказаний из папки data/history
Запуск: python analyze_history.py
"""

import os
import json
import sqlite3
from datetime import datetime
from collections import defaultdict
import glob

def analyze_history_files():
    """Анализирует файлы в папке data/history"""
    
    history_dir = 'data/history'
    
    print("="*60)
    print("📊 АНАЛИЗ ИСТОРИИ ПРЕДСКАЗАНИЙ")
    print("="*60)
    
    # 1. Проверяем наличие файлов
    print("\n1. ФАЙЛЫ В ПАПКЕ HISTORY:")
    print("-"*40)
    
    if not os.path.exists(history_dir):
        print(f"❌ Папка {history_dir} не найдена")
        return
    
    files = os.listdir(history_dir)
    if not files:
        print("❌ Папка пуста")
        return
    
    for f in files:
        filepath = os.path.join(history_dir, f)
        size = os.path.getsize(filepath)
        if size > 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"  📄 {f} ({size_str})")
    
    # 2. Проверяем базу данных SQLite
    db_path = os.path.join(history_dir, 'matches_history.db')
    if os.path.exists(db_path):
        print("\n2. АНАЛИЗ БАЗЫ ДАННЫХ (matches_history.db):")
        print("-"*40)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"  Таблицы: {[t[0] for t in tables]}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    • {table_name}: {count} записей")
        
        # Проверяем последние матчи
        try:
            cursor.execute("SELECT * FROM matches ORDER BY match_date DESC LIMIT 5")
            matches = cursor.fetchall()
            if matches:
                print(f"\n  Последние 5 матчей:")
                for match in matches:
                    print(f"    • ID: {match[0]}, {match[1]} vs {match[2]}, {match[3]}:{match[4]}")
        except:
            pass
        
        conn.close()
    
    # 3. Проверяем CSV файлы с историей
    print("\n3. АНАЛИЗ CSV ФАЙЛОВ:")
    print("-"*40)
    
    csv_files = glob.glob(os.path.join(history_dir, '*.csv'))
    if csv_files:
        for csv_file in csv_files:
            print(f"\n  📄 {os.path.basename(csv_file)}:")
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"    Строк: {len(lines)}")
                    if len(lines) > 1:
                        print(f"    Заголовок: {lines[0].strip()[:100]}")
                        print(f"    Последняя запись: {lines[-1].strip()[:100]}")
            except Exception as e:
                print(f"    Ошибка чтения: {e}")
    
    # 4. Ищем файлы предсказаний в других местах
    print("\n4. ПОИСК ПРЕДСКАЗАНИЙ В ДРУГИХ МЕСТАХ:")
    print("-"*40)
    
    prediction_files = [
        'data/predictions/predictions.json',
        'predictions.json',
        'data/predictions.json'
    ]
    
    for pf in prediction_files:
        if os.path.exists(pf):
            print(f"  ✅ Найдено: {pf}")
            try:
                with open(pf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    predictions = data.get('predictions', [])
                    print(f"     Предсказаний: {len(predictions)}")
                    
                    if predictions:
                        # Анализируем последние предсказания
                        last = predictions[-1]
                        print(f"     Последнее: {last.get('timestamp', '')[:19]} - {last.get('home_team')} vs {last.get('away_team')}")
            except Exception as e:
                print(f"     Ошибка: {e}")
    
    # 5. Статистика
    print("\n5. СТАТИСТИКА ПО ПРЕДСКАЗАНИЯМ:")
    print("-"*40)
    
    # Ищем все возможные источники предсказаний
    all_predictions = []
    
    # Из predictions.json
    for pf in prediction_files:
        if os.path.exists(pf):
            try:
                with open(pf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    preds = data.get('predictions', [])
                    all_predictions.extend(preds)
            except:
                pass
    
    # Из CSV файлов
    for csv_file in csv_files:
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_predictions.append(row)
        except:
            pass
    
    if all_predictions:
        print(f"  Всего предсказаний: {len(all_predictions)}")
        
        # Анализ по датам
        dates = defaultdict(int)
        for pred in all_predictions:
            ts = pred.get('timestamp', '')
            if ts:
                date = ts[:10] if len(ts) > 10 else ts
                dates[date] += 1
        
        if dates:
            print(f"\n  По датам:")
            for date, count in sorted(dates.items()):
                print(f"    {date}: {count} предсказаний")
        
        # Анализ по уверенности
        conf_counts = defaultdict(int)
        for pred in all_predictions:
            conf = pred.get('confidence_level', 'UNKNOWN')
            conf_counts[conf] += 1
        
        if conf_counts:
            print(f"\n  По уровню уверенности:")
            for conf, count in conf_counts.items():
                print(f"    {conf}: {count}")
        
        # Точность
        correct = sum(1 for p in all_predictions if p.get('was_correct', False))
        if correct > 0:
            print(f"\n  ✅ Сбылось: {correct}")
            print(f"  ❌ Не сбылось: {len(all_predictions) - correct}")
            print(f"  🎯 Точность: {correct/len(all_predictions)*100:.1f}%")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    analyze_history_files()