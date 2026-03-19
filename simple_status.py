# simple_status.py
import time
import os
from datetime import datetime

def simple_status():
    """Простой мониторинг без сложного парсинга"""
    
    print("="*50)
    print("ПРОСТОЙ МОНИТОРИНГ БОТА")
    print("="*50)
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"Время: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*30)
        
        # Проверяем наличие файла предсказаний
        if os.path.exists('data/predictions.json'):
            mod_time = os.path.getmtime('data/predictions.json')
            last_update = datetime.fromtimestamp(mod_time)
            time_since = (datetime.now() - last_update).total_seconds()
            
            print(f"Последнее обновление: {last_update.strftime('%H:%M:%S')}")
            print(f"Прошло: {time_since:.0f} сек")
            
            if time_since < 300:
                print("✅ БОТ РАБОТАЕТ")
            else:
                print("⚠️ БОТ НЕ АКТИВЕН")
        else:
            print("❌ Файл данных не найден")
        
        # Проверяем наличие лога
        if os.path.exists('app.log'):
            size = os.path.getsize('app.log')
            print(f"Размер лога: {size/1024:.1f} KB")
        
        print("\nНажмите Ctrl+C для выхода")
        time.sleep(5)

if __name__ == "__main__":
    simple_status()