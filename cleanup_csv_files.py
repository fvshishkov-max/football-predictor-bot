# cleanup_csv_files.py
"""
Очистка старых CSV файлов и настройка сохранения только в JSON
Запуск: python cleanup_csv_files.py
"""

import os
import shutil
from datetime import datetime

def cleanup_csv_files():
    """Перемещает или удаляет старые CSV файлы"""
    
    history_dir = 'data/history'
    
    if not os.path.exists(history_dir):
        print("❌ Папка history не найдена")
        return
    
    # Создаем папку для архива
    archive_dir = f'data/backups/csv_archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    os.makedirs(archive_dir, exist_ok=True)
    
    # Находим CSV файлы
    csv_files = [f for f in os.listdir(history_dir) if f.endswith('.csv')]
    
    print("="*60)
    print("🧹 ОЧИСТКА CSV ФАЙЛОВ")
    print("="*60)
    
    print(f"\n📁 Найдено CSV файлов: {len(csv_files)}")
    
    if csv_files:
        print(f"\n📦 Перемещаем в архив: {archive_dir}")
        
        for csv_file in csv_files:
            src = os.path.join(history_dir, csv_file)
            dst = os.path.join(archive_dir, csv_file)
            shutil.move(src, dst)
            print(f"  ✅ {csv_file}")
        
        print(f"\n✅ Перемещено {len(csv_files)} файлов")
        print(f"   Архив: {archive_dir}")
    else:
        print("\n✅ CSV файлов не найдено")
    
    # Создаем README в history
    with open(os.path.join(history_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write("""# Папка data/history

Эта папка предназначена для хранения базы данных матчей.

**Важно**: CSV файлы больше не создаются. Все данные сохраняются в:
- `data/predictions/predictions.json` - предсказания
- `data/stats/prediction_stats.json` - статистика
- `data/history/matches_history.db` - база данных матчей

Старые CSV файлы перемещены в `data/backups/csv_archive_*`
""")
    
    print("\n✅ README создан в data/history/README.md")

def check_current_saving():
    """Проверяет текущие настройки сохранения"""
    
    print("\n" + "="*60)
    print("📊 ТЕКУЩЕЕ СОСТОЯНИЕ ДАННЫХ")
    print("="*60)
    
    # Проверяем predictions.json
    if os.path.exists('data/predictions/predictions.json'):
        import json
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            predictions = data.get('predictions', [])
            print(f"\n✅ predictions.json: {len(predictions)} предсказаний")
            
            if predictions:
                last = predictions[-1]
                print(f"   Последнее: {last.get('timestamp', '')[:19]} - {last.get('home_team')} vs {last.get('away_team')}")
    
    # Проверяем логи
    if os.path.exists('data/logs/app.log'):
        size = os.path.getsize('data/logs/app.log')
        print(f"\n✅ app.log: {size} байт")
    
    # Проверяем CSV
    csv_count = len([f for f in os.listdir('data/history') if f.endswith('.csv')])
    if csv_count == 0:
        print(f"\n✅ CSV файлов в history: 0")
    else:
        print(f"\n⚠️ CSV файлов в history: {csv_count}")

if __name__ == "__main__":
    cleanup_csv_files()
    check_current_saving()