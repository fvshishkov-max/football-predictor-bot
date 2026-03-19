# check_predictions_file.py
"""
Проверка содержимого файла predictions.json
"""

import json
import os
from datetime import datetime

def check_predictions_file():
    """Проверяет структуру файла с предсказаниями"""
    
    # Пробуем разные пути
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json',
        'predictions.json'
    ]
    
    found_file = None
    for path in paths_to_try:
        if os.path.exists(path):
            found_file = path
            break
    
    if not found_file:
        print("❌ Файл с предсказаниями не найден!")
        return
    
    print(f"📁 Найден файл: {found_file}")
    print(f"📏 Размер: {os.path.getsize(found_file)} байт")
    print()
    
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 СОДЕРЖИМОЕ ФАЙЛА:")
        print("="*50)
        
        # Проверяем ключи верхнего уровня
        print(f"Ключи в файле: {list(data.keys())}")
        print()
        
        # Проверяем predictions
        predictions = data.get('predictions', [])
        print(f"Предсказаний в файле: {len(predictions)}")
        
        if predictions:
            print("\n🔍 ПЕРВОЕ ПРЕДСКАЗАНИЕ:")
            first = predictions[0]
            for key, value in first.items():
                if key != 'match':  # Пропускаем объект match
                    print(f"  {key}: {value}")
            
            print("\n🔍 ПОСЛЕДНЕЕ ПРЕДСКАЗАНИЕ:")
            last = predictions[-1]
            for key, value in last.items():
                if key != 'match':
                    print(f"  {key}: {value}")
            
            # Проверяем формат даты
            print("\n📅 ПРОВЕРКА ДАТ:")
            date_formats = {}
            for i, pred in enumerate(predictions[-10:]):  # Последние 10
                ts = pred.get('timestamp', '')
                if ts:
                    date_part = ts[:10]
                    date_formats[date_part] = date_formats.get(date_part, 0) + 1
                    print(f"  {i+1}: {ts[:19]} -> дата: {date_part}")
            
            print(f"\n📊 Распределение по датам:")
            for date, count in sorted(date_formats.items()):
                print(f"  {date}: {count} предсказаний")
        
        # Проверяем accuracy_stats
        stats = data.get('accuracy_stats', {})
        print(f"\n📊 Статистика точности:")
        print(f"  Всего предсказаний: {stats.get('total_predictions', 0)}")
        print(f"  Сигналов отправлено: {stats.get('signals_sent_46plus', 0)}")
        print(f"  Отфильтровано: {stats.get('signals_filtered_out', 0)}")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")

if __name__ == "__main__":
    check_predictions_file()