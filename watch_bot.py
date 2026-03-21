# watch_bot.py
"""
Простой мониторинг бота в реальном времени
Запуск: python watch_bot.py
"""

import json
import time
import os
from datetime import datetime

def watch():
    print("="*60)
    print("BOT MONITOR")
    print("="*60)
    print("Press Ctrl+C to stop\n")
    
    last_count = 0
    
    while True:
        try:
            now = datetime.now().strftime('%H:%M:%S')
            
            # Проверяем предсказания
            if os.path.exists('data/predictions/predictions.json'):
                with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = len(data.get('predictions', []))
                    
                    if count != last_count:
                        print(f"[{now}] Predictions: {count} (+{count - last_count})")
                        last_count = count
                    else:
                        print(f"[{now}] .", end="", flush=True)
            else:
                print(f"[{now}] No predictions file")
            
            # Проверяем логи
            if os.path.exists('data/logs/app.log'):
                with open('data/logs/app.log', 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if 'SIGNAL' in last_line or 'signal' in last_line.lower():
                            print(f"\n[{now}] LOG: {last_line[:100]}")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\nMonitor stopped")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(10)

if __name__ == "__main__":
    watch()