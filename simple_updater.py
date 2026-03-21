# simple_updater.py
"""
Простой планировщик обновлений без дополнительных зависимостей
Запуск: python simple_updater.py
"""

import time
import subprocess
from datetime import datetime

def run_command(cmd):
    """Выполняет команду и выводит результат"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Выполнение: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def main():
    print("="*70)
    print("🔄 ПРОСТОЙ ПЛАНИРОВЩИК ОБНОВЛЕНИЙ")
    print("="*70)
    print("\nРасписание:")
    print("  • Обновление результатов: каждые 30 минут")
    print("  • Проверка статистики: каждый час")
    print("\nНажмите Ctrl+C для остановки\n")
    
    last_update = 0
    last_stats = 0
    
    while True:
        try:
            now = time.time()
            
            # Обновление каждые 30 минут (1800 секунд)
            if now - last_update >= 1800:
                print("\n" + "="*70)
                print(f"🔄 ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                run_command('python auto_update_results.py')
                last_update = now
            
            # Статистика каждый час (3600 секунд)
            if now - last_stats >= 3600:
                print("\n" + "="*70)
                print(f"📊 ПРОВЕРКА СТАТИСТИКИ - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                run_command('python daily_report.py')
                last_stats = now
            
            time.sleep(60)  # Проверяем каждую минуту
            
        except KeyboardInterrupt:
            print("\n\n👋 Планировщик остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()