# show_error_lines.py
"""
Показывает проблемные строки в signal_validator.py
"""

with open('signal_validator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("="*60)
print("🔍 ПРОВЕРКА СТРОК 240-260")
print("="*60)

for i in range(239, min(260, len(lines))):
    line_num = i + 1
    line = lines[i].rstrip()
    marker = ""
    
    if line and line[-1] == '"' and line.count('"') % 2 == 1:
        marker = " <<< ВОЗМОЖНО НЕЗАКРЫТАЯ КАВЫЧКА"
    elif line and line.count('"') % 2 == 1:
        marker = " <<< НЕЧЕТНОЕ КОЛИЧЕСТВО КАВЫЧЕК"
    
    print(f"{line_num:3d}: {line}{marker}")

print("\n" + "="*60)