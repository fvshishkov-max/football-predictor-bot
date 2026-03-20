# remove_problem_method.py
"""
Удаляет проблемный метод get_false_signals_report из signal_validator.py
"""

with open('signal_validator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим и удаляем метод get_false_signals_report
new_lines = []
skip_mode = False

for line in lines:
    if 'def get_false_signals_report' in line:
        skip_mode = True
        print(f"Найден метод для удаления: {line.rstrip()}")
        continue
    
    if skip_mode and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
        skip_mode = False
    
    if not skip_mode:
        new_lines.append(line)

# Записываем обратно
with open('signal_validator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Проблемный метод удален")

# Запускаем тест
print("\n" + "="*60)
print("Запуск теста...")
print("="*60)

import subprocess
result = subprocess.run(['python', 'simple_analyze.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Ошибки:")
    print(result.stderr)