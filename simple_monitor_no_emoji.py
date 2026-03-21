# simple_monitor_no_emoji.py
"""
Simple monitor for predictions count
Запуск: python simple_monitor_no_emoji.py
"""

import json
import time
import sys
import io
from datetime import datetime

# Настраиваем вывод для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_prediction_count():
    """Get number of predictions"""
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data.get('predictions', []))
    except:
        return 0

def main():
    print("="*70)
    print("PREDICTIONS MONITOR")
    print("="*70)
    print("\nWatching predictions count...")
    print("Press Ctrl+C to stop\n")
    
    last_count = 0
    
    while True:
        try:
            count = get_prediction_count()
            now = datetime.now().strftime('%H:%M:%S')
            
            if count != last_count:
                print(f"[{now}] Predictions: {count}")
                if count >= 100:
                    print(f"\nREACHED 100 PREDICTIONS!")
                    print("Run analysis: python analyze_with_results.py\n")
                last_count = count
            else:
                print(f"[{now}] .", end="", flush=True)
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\nMonitor stopped")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()