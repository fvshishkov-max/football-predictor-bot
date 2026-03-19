# show_error_lines.py
"""
Показывает проблемные строки вокруг ошибки
"""

import sys

def show_lines():
    """Показывает строки 650-680"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("="*60)
    print("🔍 ПРОВЕРКА СТРОК 650-680")
    print("="*60)
    
    start = 650
    end = min(680, len(lines))
    
    for i in range(start-1, end):
        line_num = i + 1
        line = lines[i].rstrip()
        
        # Отмечаем потенциальные проблемы
        marker = ""
        if 'return Falsedef' in line:
            marker = " <<< ПРОБЛЕМА! Методы склеены"
        elif line.startswith('    def ') and not line.startswith('        def'):
            marker = " <<< Начало метода"
        elif line.strip() and not line[0].isspace():
            marker = " <<< Вне отступа?"
        
        print(f"{line_num:4d}: {line}{marker}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    show_lines()