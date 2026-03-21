# force_save_predictions.py
"""
Принудительно сохраняет текущие предсказания в JSON
"""

import json
import os
import glob
from datetime import datetime

def force_save():
    """Собирает все данные из CSV и сохраняет в JSON"""
    
    print("="*60)
    print("💾 ПРИНУДИТЕЛЬНОЕ СОХРАНЕНИЕ ДАННЫХ")
    print("="*60)
    
    all_predictions = []
    
    # 1. Собираем из CSV файлов в history
    history_dir = 'data/history'
    if os.path.exists(history_dir):
        csv_files = glob.glob(os.path.join(history_dir, '*.csv'))
        print(f"\n📁 Найдено CSV файлов: {len(csv_files)}")
        
        for csv_file in csv_files[-10:]:  # Берем последние 10
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        print(f"  📄 {os.path.basename(csv_file)}: {len(lines)-1} записей")
            except:
                pass
    
    # 2. Загружаем существующий JSON
    json_file = 'data/predictions/predictions.json'
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing = data.get('predictions', [])
            print(f"\n📊 Существующих предсказаний в JSON: {len(existing)}")
            all_predictions.extend(existing)
    
    # 3. Сохраняем
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Сохранено: {len(all_predictions)} предсказаний")
    print(f"📁 Файл: {json_file}")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    force_save()