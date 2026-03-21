# simple_updater_no_emoji.py
"""
Простой планировщик обновлений без эмодзи
Запуск: python simple_updater_no_emoji.py
"""

import time
import subprocess
import sys
import io
from datetime import datetime

# Настраиваем вывод для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_command(cmd):
    """Выполняет команду и выводит результат"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def main():
    print("="*70)
    print("SIMPLE UPDATE SCHEDULER")
    print("="*70)
    print("\nSchedule:")
    print("  • Update results: every 30 minutes")
    print("  • Check statistics: every hour")
    print("\nPress Ctrl+C to stop\n")
    
    last_update = 0
    last_stats = 0
    
    while True:
        try:
            now = time.time()
            
            # Update every 30 minutes (1800 seconds)
            if now - last_update >= 1800:
                print("\n" + "="*70)
                print(f"UPDATE RESULTS - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                run_command('python auto_update_results.py')
                last_update = now
            
            # Statistics every hour (3600 seconds)
            if now - last_stats >= 3600:
                print("\n" + "="*70)
                print(f"CHECK STATISTICS - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                run_command('python daily_report.py')
                last_stats = now
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n\nScheduler stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()