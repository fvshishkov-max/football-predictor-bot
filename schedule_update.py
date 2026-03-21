# schedule_update.py
"""
Автоматическое обновление результатов по расписанию
Запуск: python schedule_update.py
"""

import time
import schedule
import subprocess
from datetime import datetime

def update_results():
    """Обновляет результаты через API"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Обновление результатов...")
    subprocess.run(['python', 'auto_update_results.py'], capture_output=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Обновление завершено")

def analyze_stats():
    """Анализирует статистику"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Анализ статистики...")
    subprocess.run(['python', 'analyze_with_results.py'], capture_output=True)

def main():
    print("="*70)
    print("⏰ ПЛАНИРОВЩИК ОБНОВЛЕНИЙ")
    print("="*70)
    print("\nРасписание:")
    print("  • Обновление результатов: каждый час")
    print("  • Анализ статистики: каждый день в 00:00")
    print("\nНажмите Ctrl+C для остановки\n")
    
    # Запускаем обновление раз в час
    schedule.every(1).hours.do(update_results)
    
    # Запускаем анализ раз в сутки
    schedule.every().day.at("00:00").do(analyze_stats)
    
    # Первое обновление сразу
    update_results()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Планировщик остановлен")