# cleanup.py
import os
import glob
from datetime import datetime, timedelta

def cleanup_old_files(days_to_keep=7):
    """Удаляет старые файлы истории"""
    
    print("🧹 ОЧИСТКА СТАРЫХ ФАЙЛОВ")
    print("="*60)
    print(f"📅 Оставляем файлы за последние {days_to_keep} дней")
    
    # Текущее время
    now = datetime.now()
    cutoff = now - timedelta(days=days_to_keep)
    
    # Собираем все файлы истории
    signal_files = glob.glob('signals_history_*.json')
    csv_files = glob.glob('signals_history_*.csv')
    
    all_files = signal_files + csv_files
    
    # Сортируем по дате
    files_with_dates = []
    for file in all_files:
        try:
            # Извлекаем дату из имени файла
            # signals_history_20260311_140346.json
            date_str = file.split('_')[2]
            if len(date_str) == 8:  # YYYYMMDD
                file_date = datetime.strptime(date_str, '%Y%m%d')
                files_with_dates.append((file, file_date))
        except:
            continue
    
    # Сортируем по дате
    files_with_dates.sort(key=lambda x: x[1])
    
    # Удаляем старые файлы
    deleted = 0
    kept = 0
    
    for file, file_date in files_with_dates:
        if file_date < cutoff:
            try:
                os.remove(file)
                print(f"❌ Удален: {file}")
                deleted += 1
            except Exception as e:
                print(f"⚠️ Ошибка удаления {file}: {e}")
        else:
            kept += 1
    
    print(f"\n📊 ИТОГ:")
    print(f"   Удалено файлов: {deleted}")
    print(f"   Оставлено файлов: {kept}")
    print("="*60)

if __name__ == "__main__":
    cleanup_old_files(7)