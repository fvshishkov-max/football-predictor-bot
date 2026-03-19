# monitor_queue.py
import time
import psutil
import os
from datetime import datetime

def monitor_queue():
    """Мониторит размер очереди сообщений"""
    while True:
        try:
            # Проверяем размер файла очереди (если есть)
            if os.path.exists('message_queue.log'):
                size = os.path.getsize('message_queue.log')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Queue size: {size} bytes")
            
            # Проверяем использование памяти
            process = psutil.Process()
            memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"Memory usage: {memory:.1f} MB")
            
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except:
            time.sleep(5)

if __name__ == "__main__":
    monitor_queue()