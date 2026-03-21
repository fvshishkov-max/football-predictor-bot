# simple_monitor.py
"""
Простой мониторинг количества предсказаний
Запуск: python simple_monitor.py
"""

import json
import time
import os
from datetime import datetime

def get_prediction_count():
    """Получает количество предсказаний"""
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data.get('predictions', []))
    except:
        return 0

def main():
    print("="*70)
    print("📊 МОНИТОРИНГ ПРЕДСКАЗАНИЙ")
    print("="*70)
    print("\nСлежу за количеством предсказаний...")
    print("Нажмите Ctrl+C для остановки\n")
    
    last_count = 0
    
    while True:
        try:
            count = get_prediction_count()
            now = datetime.now().strftime('%H:%M:%S')
            
            if count != last_count:
                print(f"[{now}] 📊 Предсказаний: {count}")
                if count >= 100:
                    print(f"\n✅ ДОСТИГНУТО 100 ПРЕДСКАЗАНИЙ!")
                    print("Можно запускать полный анализ: python analyze_with_results.py\n")
                last_count = count
            else:
                print(f"[{now}] .", end="", flush=True)
            
            time.sleep(30)  # Проверяем каждые 30 секунд
            
        except KeyboardInterrupt:
            print("\n\n👋 Мониторинг остановлен")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()