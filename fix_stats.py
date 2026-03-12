# fix_stats.py
import json
from datetime import datetime
import glob
import os

print("🔧 ИСПРАВЛЕНИЕ СТАТИСТИКИ")
print("="*60)

# 1. Загружаем bot_stats.json
try:
    with open('bot_stats.json', 'r', encoding='utf-8') as f:
        bot_stats = json.load(f)
    print(f"✅ bot_stats.json загружен")
    print(f"   Сигналов отправлено: {bot_stats['total_signals_sent']}")
    print(f"   Голов подтверждено: {bot_stats['total_goals_confirmed']}")
except Exception as e:
    print(f"❌ Ошибка загрузки bot_stats.json: {e}")
    bot_stats = {'total_signals_sent': 0, 'total_goals_confirmed': 0}

# 2. Загружаем все файлы истории сигналов
all_signals = []
signal_files = glob.glob('signals_history_*.json')
if signal_files:
    for file in signal_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                signals = json.load(f)
                if isinstance(signals, list):
                    all_signals.extend(signals)
            print(f"✅ {file}: {len(signals)} сигналов")
        except Exception as e:
            print(f"❌ Ошибка загрузки {file}: {e}")

# 3. Удаляем дубликаты
unique_signals = {}
for s in all_signals:
    key = (s.get('match_id'), s.get('signal_minute'))
    if key not in unique_signals:
        unique_signals[key] = s

print(f"\n📊 Всего уникальных сигналов: {len(unique_signals)}")

# 4. Подсчитываем реальную статистику по логам
# Вручную вносим неточные сигналы из логов
# Матч 1421621: прогноз ~45', реальный 15', ошибка 30 мин (неточный)
# Матч 1421621: прогноз ~45', реальный 19', ошибка 26 мин (неточный)
# Матч 1421621: прогноз ~45', реальный 20', ошибка 25 мин (неточный)
# Матч 1421621: прогноз ~60', реальный 28', ошибка 32 мин (неточный)
# Матч 1497885: прогноз ~60', реальный 22', ошибка 38 мин (неточный)

# Обновляем записи в unique_signals
for key in list(unique_signals.keys()):
    s = unique_signals[key]
    match_id = s.get('match_id')
    signal_minute = s.get('signal_minute')
    
    # Помечаем неточные сигналы
    if match_id == 1421621:
        if signal_minute == 45:
            s['actual_goal_minute'] = 19
            s['was_correct'] = False
            s['time_error'] = 26
        elif signal_minute == 60:
            s['actual_goal_minute'] = 28
            s['was_correct'] = False
            s['time_error'] = 32
    elif match_id == 1497885 and signal_minute == 60:
        s['actual_goal_minute'] = 22
        s['was_correct'] = False
        s['time_error'] = 38

# 5. Подсчитываем исправленную статистику
total_signals = len(unique_signals)
confirmed_goals = sum(1 for s in unique_signals.values() if s.get('actual_goal_minute'))
correct_signals = sum(1 for s in unique_signals.values() if s.get('was_correct') == True)
total_error = sum(s.get('time_error', 0) for s in unique_signals.values() if s.get('time_error'))

accuracy_rate = (correct_signals / total_signals * 100) if total_signals > 0 else 0
avg_error = total_error / correct_signals if correct_signals > 0 else 0

# 6. Создаем исправленную статистику
fixed_stats = {
    "stats": {
        "total_signals": total_signals,
        "correct_signals": correct_signals,
        "accuracy_rate": accuracy_rate,
        "avg_time_error": avg_error,
        "goals_predicted": total_signals,
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

# 7. Сохраняем исправленную статистику
if os.path.exists('signal_accuracy.json'):
    backup_name = f'signal_accuracy_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.rename('signal_accuracy.json', backup_name)
    print(f"✅ Создан бэкап: {backup_name}")

with open('signal_accuracy.json', 'w', encoding='utf-8') as f:
    json.dump(fixed_stats, f, ensure_ascii=False, indent=2)

print("\n📊 ИСПРАВЛЕННАЯ СТАТИСТИКА:")
print(f"   Всего сигналов: {total_signals}")
print(f"   Точных: {correct_signals}")
print(f"   Точность: {accuracy_rate:.1f}%")
print(f"   Средняя ошибка: {avg_error:.1f} мин")
print(f"   Всего голов: {fixed_stats['stats']['goals_actual']}")
print("="*60)
print("✅ signal_accuracy.json обновлен!")