# fix_strings.py
"""
Быстрое исправление проблем с кавычками в файлах
"""

import os

def fix_signal_validator():
    """Исправляет проблемы с кавычками в signal_validator.py"""
    
    if not os.path.exists('signal_validator.py'):
        print("❌ signal_validator.py не найден")
        return
    
    with open('signal_validator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем проблемную строку 251
    lines = content.split('\n')
    if len(lines) >= 251:
        # Заменяем строку с отчетом
        lines[250] = '        report = "📊 **ОТЧЕТ ПО ЛОЖНЫМ СИГНАЛАМ**"'
        print(f"✅ Исправлена строка 251")
    
    # Также проверим другие возможные проблемы
    for i, line in enumerate(lines):
        if 'report = "📊' in line and not line.strip().endswith('"'):
            lines[i] = line.rstrip() + '"'
            print(f"✅ Исправлена строка {i+1}")
    
    new_content = '\n'.join(lines)
    
    with open('signal_validator.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ signal_validator.py исправлен")

def fix_analyze_false():
    """Исправляет проблемы с кавычками в analyze_false_signals.py"""
    
    if not os.path.exists('analyze_false_signals.py'):
        print("❌ analyze_false_signals.py не найден")
        return
    
    with open('analyze_false_signals.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем возможные проблемы с экранированием
    content = content.replace('\\n', '\n')
    content = content.replace('\\"', '"')
    
    with open('analyze_false_signals.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ analyze_false_signals.py исправлен")

def main():
    print("="*60)
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С КАВЫЧКАМИ")
    print("="*60)
    
    fix_signal_validator()
    fix_analyze_false()
    
    print("\n" + "="*60)
    print("✅ ГОТОВО! Теперь запустите:")
    print("  scripts\\analyze_false.bat")
    print("="*60)

if __name__ == "__main__":
    main()