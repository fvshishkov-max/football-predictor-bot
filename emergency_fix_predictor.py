# emergency_fix_predictor.py
"""
Экстренное исправление predictor.py
"""

def emergency_fix():
    """Исправляет склеенные методы"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем проблемное место
    print("Поиск проблемных мест...")
    
    # Исправляем склеенные методы
    fixes = [
        ('return Falsedef _extract_team_stats', 'return False\n\n    def _extract_team_stats'),
        ('return Falsedef _save_match_to_history', 'return False\n\n    def _save_match_to_history'),
        ('return Falsedef update_accuracy', 'return False\n\n    def update_accuracy'),
        ('return Falsedef _add_to_history', 'return False\n\n    def _add_to_history'),
        ('return Falsedef _get_default_prediction', 'return False\n\n    def _get_default_prediction'),
    ]
    
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Исправлено: {old[:30]}...")
    
    # Также ищем метод _should_analyze_match и проверяем его
    if 'def _should_analyze_match' in content:
        print("✅ Метод _should_analyze_match найден")
    
    # Сохраняем исправленный файл
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Исправления применены!")
    
    # Проверяем синтаксис
    import py_compile
    try:
        py_compile.compile('predictor.py', doraise=True)
        print("✅ Синтаксис исправлен!")
    except py_compile.PyCompileError as e:
        print(f"❌ Остались ошибки: {e}")

if __name__ == "__main__":
    emergency_fix()