# final_fix_predictor.py
"""
Окончательное исправление отступов в predictor.py
"""

def final_fix():
    """Исправляет отступы в методе _should_analyze_match"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔧 ИСПРАВЛЕНИЕ ОТСТУПОВ")
    print("="*50)
    
    # Находим метод _should_analyze_match
    start_line = -1
    for i, line in enumerate(lines):
        if 'def _should_analyze_match' in line:
            start_line = i
            print(f"✅ Найден метод на строке {i+1}")
            break
    
    if start_line == -1:
        print("❌ Метод не найден")
        return
    
    # Исправляем отступы в методе
    fixed_lines = []
    i = start_line
    
    # Добавляем заголовок метода
    fixed_lines.append(lines[i])  # def _should_analyze_match...
    i += 1
    
    # Исправляем докстринг (должен иметь отступ в 4 пробела)
    if i < len(lines) and '"""' in lines[i]:
        fixed_lines.append('    ' + lines[i].lstrip())
        i += 1
    else:
        fixed_lines.append('    """Улучшенная проверка с использованием MatchFilter"""\n')
    
    # Добавляем пустую строку с отступом
    fixed_lines.append('    \n')
    
    # Копируем остальные строки метода с правильными отступами
    while i < len(lines):
        line = lines[i]
        
        # Если нашли следующий метод на том же уровне - выходим
        if line.strip().startswith('def ') and not line.startswith('    def '):
            break
        
        # Добавляем строку с отступом 4 пробела
        if line.strip():
            fixed_lines.append('    ' + line.lstrip())
        else:
            fixed_lines.append('    \n')
        
        i += 1
    
    # Добавляем пустую строку после метода
    fixed_lines.append('\n')
    
    # Собираем новый файл
    new_lines = lines[:start_line] + fixed_lines + lines[i:]
    
    # Записываем обратно
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Отступы исправлены")
    
    # Проверяем синтаксис
    import py_compile
    try:
        py_compile.compile('predictor.py', doraise=True)
        print("✅ Синтаксис в порядке!")
    except py_compile.PyCompileError as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    final_fix()