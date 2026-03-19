# sync_stats.py
import json
import os
from datetime import datetime
import glob

def sync_stats():
    """Синхронизирует статистику между файлами"""
    
    print("🔄 СИНХРОНИЗАЦИЯ СТАТИСТИКИ")
    print("="*60)
    
    # 1. Загружаем bot_stats.json
    if os.path.exists('bot_stats.json'):
        with open('bot_stats.json', 'r', encoding='utf-8') as f:
            bot_stats = json.load(f)
        print(f"✅ bot_stats.json: {bot_stats['total_signals_sent']} отправлено, {bot_stats['total_goals_confirmed']} голов")
    else:
        bot_stats = {
            'last_processed_goals': {},
            'sent_signals': [],
            'processed_matches': [],
            'last_restart': datetime.now().isoformat(),
            'total_signals_sent': 0,
            'total_goals_confirmed': 0,
            'bot_version': '2.0'
        }
        print("⚠️ bot_stats.json не найден, создаем новый")
    
    # 2. Загружаем последний файл истории
    signal_files = glob.glob('signals_history_*.json')
    if signal_files:
        latest = max(signal_files)
        with open(latest, 'r', encoding='utf-8') as f:
            signals = json.load(f)
        print(f"✅ {latest}: {len(signals)} сигналов")
    else:
        signals = []
        print("⚠️ Файлы истории не найдены")
    
    # 3. Подсчитываем сигналы из истории
    total_signals_in_history = len(signals)
    confirmed_goals = sum(1 for s in signals if s.get('actual_goal_minute'))
    correct_signals = sum(1 for s in signals if s.get('was_correct') == True)
    
    print(f"\n📊 Статистика из истории:")
    print(f"   Всего сигналов: {total_signals_in_history}")
    print(f"   Подтверждено голов: {confirmed_goals}")
    print(f"   Точных сигналов: {correct_signals}")
    
    # 4. Создаем синхронизированную статистику
    total_error = sum(s.get('time_error', 0) for s in signals if s.get('time_error'))
    avg_error = total_error / correct_signals if correct_signals > 0 else 0
    accuracy_rate = (correct_signals / total_signals_in_history * 100) if total_signals_in_history > 0 else 0
    
    synced_stats = {
        "stats": {
            "total_signals": total_signals_in_history,
            "correct_signals": correct_signals,
            "accuracy_rate": accuracy_rate,
            "avg_time_error": avg_error,
            "goals_predicted": total_signals_in_history,
            "goals_actual": bot_stats['total_goals_confirmed']
        },
        "params": {
            "shots_per_goal": 9.5,
            "ontarget_per_goal": 3.8,
            "corners_per_goal": 5.2,
            "dangerous_attack_per_goal": 2.5,
            "min_minutes_for_analysis": 5,
            "probability_threshold": 0.5,
            "high_probability_threshold": 0.7
        },
        "last_updated": datetime.now().isoformat()
    }
    
    # 5. Сохраняем синхронизированную статистику
    if os.path.exists('signal_accuracy.json'):
        backup_name = f'signal_accuracy_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.rename('signal_accuracy.json', backup_name)
        print(f"✅ Создан бэкап: {backup_name}")
    
    with open('signal_accuracy.json', 'w', encoding='utf-8') as f:
        json.dump(synced_stats, f, ensure_ascii=False, indent=2)
    
    print("\n📊 СИНХРОНИЗИРОВАННАЯ СТАТИСТИКА:")
    print(f"   Всего сигналов: {total_signals_in_history}")
    print(f"   Точных: {correct_signals}")
    print(f"   Точность: {accuracy_rate:.1f}%")
    print(f"   Средняя ошибка: {avg_error:.1f} мин")
    print(f"   Всего голов: {synced_stats['stats']['goals_actual']}")
    print("="*60)
    print("✅ signal_accuracy.json синхронизирован!")

if __name__ == "__main__":
    sync_stats()