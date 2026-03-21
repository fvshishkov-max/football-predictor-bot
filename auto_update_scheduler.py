# auto_update_scheduler.py
"""
Автоматическое обновление результатов по расписанию
Запуск: python auto_update_scheduler.py
"""

import time
import subprocess
from datetime import datetime

def update_results():
    """Обновляет результаты"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Обновление результатов...")
    subprocess.run(['python', 'update_results_from_api.py'], capture_output=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Обновление завершено")

def main():
    print("="*80)
    print("⏰ АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*80)
    print("\nРасписание:")
    print("  • Обновление результатов: каждый час")
    print("\nНажмите Ctrl+C для остановки\n")
    
    last_update = time.time()
    
    while True:
        try:
            now = time.time()
            
            # Обновление каждый час (3600 секунд)
            if now - last_update >= 3600:
                update_results()
                last_update = now
            
            time.sleep(60)  # Проверяем каждую минуту
            
        except KeyboardInterrupt:
            print("\n\n👋 Планировщик остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()