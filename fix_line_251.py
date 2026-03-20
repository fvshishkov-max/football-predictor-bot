# fix_line_251.py
"""
Исправляет конкретную строку 251 в signal_validator.py
"""

# Читаем файл
with open('signal_validator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Исправляем строку 251 (индекс 250)
if len(lines) >= 251:
    print(f"Строка 251 сейчас: {lines[250].rstrip()}")
    
    # Правильная строка
    lines[250] = '        report = "📊 **ОТЧЕТ ПО ЛОЖНЫМ СИГНАЛАМ**"\n'
    
    print(f"Строка 251 исправлена на: {lines[250].rstrip()}")
else:
    print(f"В файле только {len(lines)} строк, нет строки 251")

# Записываем обратно
with open('signal_validator.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ signal_validator.py исправлен")

# Проверяем следующие строки на подобные проблемы
for i, line in enumerate(lines):
    if 'report = "' in line and not line.strip().endswith('"') and not line.strip().endswith('+'):
        print(f"Найдена проблема в строке {i+1}: {line.rstrip()}")
        # Исправляем если нужно
        lines[i] = line.rstrip() + '"\n'

# Записываем снова если были исправления
with open('signal_validator.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Проверка завершена")

# Запускаем тест
print("\n" + "="*60)
print("Запуск теста...")
print("="*60)

import subprocess
subprocess.run(['python', 'simple_analyze.py'])