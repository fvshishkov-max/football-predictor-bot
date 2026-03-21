# monitor_saving.py
"""
Мониторинг сохранения данных в реальном времени
Запуск: python monitor_saving.py
"""

import os
import json
import time
from datetime import datetime

def monitor_saving():
    """Следит за изменениями в predictions.json"""
    
    print("="*60)
    print("📊 МОНИТОРИНГ СОХРАНЕНИЯ ДАННЫХ")
    print("="*60)
    print("\nСлежу за изменениями в predictions.json...")
    print("Нажмите Ctrl+C для остановки\n")
    
    last_size = 0
    last_count = 0
    
    while True:
        try:
            # Проверяем файл predictions.json
            if os.path.exists('data/predictions/predictions.json'):
                size = os.path.getsize('data/predictions/predictions.json')
                mod_time = datetime.fromtimestamp(os.path.getmtime('data/predictions/predictions.json'))
                
                if size != last_size:
                    print(f"\n{'='*60}")
                    print(f"🔄 ИЗМЕНЕНИЕ В {mod_time.strftime('%H:%M:%S')}")
                    print(f"{'='*60}")
                    
                    # Читаем содержимое
                    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        predictions = data.get('predictions', [])
                        
                    print(f"📊 Предсказаний: {len(predictions)}")
                    print(f"📏 Размер файла: {size} байт")
                    
                    if predictions:
                        last_pred = predictions[-1]
                        print(f"\n📋 ПОСЛЕДНЕЕ ПРЕДСКАЗАНИЕ:")
                        print(f"   Матч: {last_pred.get('home_team')} vs {last_pred.get('away_team')}")
                        print(f"   Время: {last_pred.get('timestamp', '')[:19]}")
                        print(f"   Вероятность: {last_pred.get('goal_probability', 0)*100:.1f}%")
                        print(f"   Сбылось: {'✅' if last_pred.get('was_correct') else '❓'}")
                    
                    last_size = size
                    last_count = len(predictions)
                else:
                    print(".", end="", flush=True)
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n👋 Мониторинг остановлен")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_saving()