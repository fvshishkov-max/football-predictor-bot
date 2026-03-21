# check_predictions_live.py
"""
Проверка, пишутся ли предсказания в реальном времени
Запуск: python check_predictions_live.py
"""

import json
import time
import os
from datetime import datetime

def check_predictions():
    """Проверяет, появляются ли новые предсказания"""
    
    pred_file = 'data/predictions/predictions.json'
    last_count = 0
    last_modified = 0
    
    print("="*80)
    print("🔍 МОНИТОРИНГ ПРЕДСКАЗАНИЙ В РЕАЛЬНОМ ВРЕМЕНИ")
    print("="*80)
    print("\nСлежу за появлением новых предсказаний...")
    print("Нажмите Ctrl+C для остановки\n")
    
    while True:
        try:
            if os.path.exists(pred_file):
                # Проверяем размер и время изменения
                current_size = os.path.getsize(pred_file)
                current_modified = os.path.getmtime(pred_file)
                
                if current_modified != last_modified:
                    # Файл изменился!
                    print(f"\n{'='*80}")
                    print(f"🔄 ИЗМЕНЕНИЕ ОБНАРУЖЕНО! {datetime.now().strftime('%H:%M:%S')}")
                    print(f"{'='*80}")
                    
                    with open(pred_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    predictions = data.get('predictions', [])
                    stats = data.get('accuracy_stats', {})
                    
                    print(f"\n📊 Всего предсказаний: {len(predictions)}")
                    print(f"   Изменение: +{len(predictions) - last_count}")
                    print(f"   Размер файла: {current_size} байт")
                    
                    if predictions:
                        last_pred = predictions[-1]
                        print(f"\n📋 ПОСЛЕДНЕЕ ПРЕДСКАЗАНИЕ:")
                        print(f"   Время: {last_pred.get('timestamp', '')[:19]}")
                        print(f"   Матч: {last_pred.get('home_team')} vs {last_pred.get('away_team')}")
                        print(f"   Минута: {last_pred.get('minute', 0)}'")
                        print(f"   Вероятность: {last_pred.get('goal_probability', 0)*100:.1f}%")
                        print(f"   Уверенность: {last_pred.get('confidence_level', 'UNKNOWN')}")
                        print(f"   Сигнал: {'✅' if last_pred.get('signal') else '❌'}")
                        print(f"   Результат: {'✅' if last_pred.get('was_correct') else ('❌' if last_pred.get('was_correct') is False else '❓')}")
                    
                    print(f"\n📊 СТАТИСТИКА:")
                    print(f"   Всего предсказаний: {stats.get('total_predictions', 0)}")
                    print(f"   Правильных: {stats.get('correct_predictions', 0)}")
                    print(f"   Точность: {stats.get('accuracy_rate', 0)*100:.1f}%")
                    print(f"   Сигналов отправлено: {stats.get('signals_sent_46plus', 0)}")
                    
                    last_count = len(predictions)
                    last_modified = current_modified
                
                # Показываем точки ожидания
                print(".", end="", flush=True)
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n👋 Мониторинг остановлен")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    check_predictions()