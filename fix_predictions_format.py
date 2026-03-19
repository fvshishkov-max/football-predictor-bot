# fix_predictions_format.py
"""
Исправляет формат дат в файле predictions.json
"""

import json
import os
from datetime import datetime

def fix_predictions_format():
    """Исправляет формат дат в предсказаниях"""
    
    # Пробуем разные пути
    paths_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
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
    
    try:
        with open(found_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Загружено {len(data.get('predictions', []))} предсказаний")
        
        # Исправляем форматы дат
        predictions = data.get('predictions', [])
        fixed_count = 0
        
        for pred in predictions:
            ts = pred.get('timestamp')
            if ts and isinstance(ts, str):
                # Проверяем, нужно ли исправлять
                if 'T' not in ts and ' ' in ts:
                    # Формат "YYYY-MM-DD HH:MM:SS" -> ISO
                    try:
                        dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                        pred['timestamp'] = dt.isoformat()
                        fixed_count += 1
                    except:
                        pass
                elif len(ts) == 10 and '-' in ts:  # Только дата
                    try:
                        dt = datetime.strptime(ts, '%Y-%m-%d')
                        pred['timestamp'] = dt.isoformat()
                        fixed_count += 1
                    except:
                        pass
        
        print(f"✅ Исправлено {fixed_count} записей")
        
        # Сохраняем обратно
        with open(found_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ Файл сохранен")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_predictions_format()