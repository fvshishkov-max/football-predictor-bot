# fix_syntax.py
"""
Исправление синтаксической ошибки в predictor.py
"""

import re

def fix_syntax():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Ищем проблемную строку
    for i, line in enumerate(lines):
        if 'goal_probability = goal_probability' in line:
            print(f"Found problematic line at {i+1}: {line.strip()}")
            # Заменяем на правильный код
            lines[i] = '        goal_probability = goal_probability\n'
            
            # Добавляем недостающие строки
            lines.insert(i+1, '        \n')
    
    # Проверяем, что блок try/except корректен
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и исправляем проблемный участок вручную
    correct_block = '''            # Калибруем вероятность
            goal_probability = self._calibrate_probability(goal_probability)
            
            # Убираем random вариацию для стабильности
            # variation = random.uniform(0.95, 1.05)
            # goal_probability = min(0.95, max(0.1, goal_probability * variation))
            # Используем только калиброванную вероятность
            goal_probability = goal_probability
            
            # Определяем уровень уверенности
            confidence_level = self._determine_confidence_level(goal_probability)'''
    
    # Ищем старый блок и заменяем
    old_pattern = r'# Калибруем вероятность.*?confidence_level = self\._determine_confidence_level\(goal_probability\)'
    new_content = re.sub(old_pattern, correct_block, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fixed syntax error")
    
    # Проверяем синтаксис
    import py_compile
    try:
        py_compile.compile('predictor.py', doraise=True)
        print("✅ Syntax is correct")
    except py_compile.PyCompileError as e:
        print(f"❌ Still has errors: {e}")

if __name__ == "__main__":
    fix_syntax()