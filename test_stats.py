# test_stats.py
import json
from datetime import datetime

def test_stats_saving():
    """Тестирует сохранение статистики"""
    
    print("🔍 ТЕСТ СОХРАНЕНИЯ СТАТИСТИКИ")
    print("="*40)
    
    # Проверяем signal_accuracy.json
    try:
        with open('signal_accuracy.json', 'r', encoding='utf-8') as f:
            stats = json.load(f)
            print(f"✅ signal_accuracy.json загружен")
            print(f"   Статистика: {stats['stats']}")
    except Exception as e:
        print(f"❌ Ошибка загрузки signal_accuracy.json: {e}")
    
    # Проверяем последний файл истории
    import glob
    signal_files = glob.glob('signals_history_*.json')
    if signal_files:
        latest = max(signal_files)
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                signals = json.load(f)
                print(f"✅ {latest} загружен")
                print(f"   Сигналов: {len(signals)}")
        except Exception as e:
            print(f"❌ Ошибка загрузки {latest}: {e}")
    else:
        print("❌ Файлы истории сигналов не найдены")
    
    # Проверяем лог-файл
    try:
        with open('football_bot.log', 'r', encoding='utf-8') as f:
            log_size = len(f.read())
            print(f"✅ football_bot.log: {log_size} байт")
    except Exception as e:
        print(f"❌ Ошибка чтения лога: {e}")
    
    print("="*40)

if __name__ == "__main__":
    test_stats_saving()