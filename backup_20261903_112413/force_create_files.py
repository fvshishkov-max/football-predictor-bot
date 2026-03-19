# force_create_files.py
import json
import os
from datetime import datetime

print("🔧 Принудительное создание необходимых файлов...")

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

# 2. Создаем пустую историю сигналов
signals_history = []

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
with open(f'signals_history_{timestamp}.json', 'w', encoding='utf-8') as f:
    json.dump(signals_history, f, ensure_ascii=False, indent=2)
print(f"✅ signals_history_{timestamp}.json создан")

# 3. Создаем файл лога
with open('football_bot.log', 'w', encoding='utf-8') as f:
    f.write(f"{datetime.now().isoformat()} - Создан файл лога\n")
print("✅ football_bot.log создан")

# 4. Создаем папки
if not os.path.exists('logs'):
    os.makedirs('logs')
    print("✅ Папка logs создана")

if not os.path.exists('signals'):
    os.makedirs('signals')
    print("✅ Папка signals создана")

print("\n🎉 Все файлы успешно созданы!")
print("📁 Список созданных файлов:")
for file in os.listdir('.'):
    if file.endswith('.json') or file.endswith('.log'):
        print(f"   • {file}")