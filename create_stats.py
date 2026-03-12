# create_stats.py
import json
from datetime import datetime

print("🔧 СОЗДАНИЕ ФАЙЛОВ СТАТИСТИКИ")
print("="*40)

# 1. Создаем signal_accuracy.json
signal_accuracy = {
    "stats": {
        "total_signals": 0,
        "correct_signals": 0,
        "accuracy_rate": 0,
        "avg_time_error": 0,
        "goals_predicted": 0,
        "goals_actual": 0
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

with open('signal_accuracy.json', 'w', encoding='utf-8') as f:
    json.dump(signal_accuracy, f, ensure_ascii=False, indent=2)
print("✅ signal_accuracy.json создан")

# 2. Создаем тестовую историю сигналов из bot_stats.json
try:
    with open('bot_stats.json', 'r', encoding='utf-8') as f:
        bot_stats = json.load(f)
    
    signals = []
    for match_id, goals in bot_stats['last_processed_goals'].items():
        for goal_minute in goals:
            signals.append({
                'timestamp': datetime.now().isoformat(),
                'match_id': int(match_id),
                'home_team': 'Unknown',
                'away_team': 'Unknown',
                'signal_minute': goal_minute,
                'signal_probability': 70.0,
                'actual_goal_minute': goal_minute,
                'was_correct': True,
                'match_minute': goal_minute,
                'score': '1:0'
            })
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'signals_history_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)
    print(f"✅ signals_history_{timestamp}.json создан с {len(signals)} сигналами")
    
except Exception as e:
    print(f"❌ Ошибка создания истории сигналов: {e}")

# 3. Проверяем лог-файл
with open('football_bot.log', 'a', encoding='utf-8') as f:
    f.write(f"{datetime.now().isoformat()} - Файлы статистики созданы\n")
print("✅ football_bot.log обновлен")

print("="*40)
print("🎉 Готово! Теперь можно запускать мониторинг:")
print("python real_time_analyzer_simple.py")