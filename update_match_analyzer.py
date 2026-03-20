# update_match_analyzer.py
"""
Обновляет match_analyzer.py с новыми порогами на основе статистики
"""

import json
import os

def update_analyzer_with_stats():
    """Обновляет анализатор на основе накопленной статистики"""
    
    # Читаем текущие настройки
    with open('match_analyzer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновляем пороги для времени (оптимальные значения)
    time_factors = {
        '0-15': 0.5,    # Низкая вероятность
        '15-30': 0.8,   # Средняя
        '30-45': 1.0,   # Хорошая
        '45-60': 0.9,   # После перерыва
        '60-75': 1.1,   # Высокая
        '75-90': 1.4,   # Максимальная
        '90+': 0.6,     # Добавленное время - рискованно
    }
    
    # Обновляем метод _calculate_time_factor
    new_time_method = '''
    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор оставшегося времени (оптимизированный)"""
        if not minute:
            return 1.0
        if minute < 15:
            return 0.5   # Начало матча - низкая вероятность
        elif minute < 30:
            return 0.8   # Первые минуты разогрева
        elif minute < 45:
            return 1.0   # Пик первого тайма
        elif minute < 60:
            return 0.9   # После перерыва
        elif minute < 75:
            return 1.1   # Середина второго тайма
        elif minute < 90:
            return 1.4   # Концовка - самое опасное время
        else:
            return 0.6   # Добавленное время - рискованно'''
    
    # Заменяем старый метод
    import re
    pattern = r'def _calculate_time_factor\(self, minute: int\) -> float:.*?return [0-9.]+'
    new_content = re.sub(pattern, new_time_method, content, flags=re.DOTALL)
    
    with open('match_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ match_analyzer.py обновлен с оптимизированными временными факторами")
    print()
    print("📊 НОВЫЕ ФАКТОРЫ ВРЕМЕНИ:")
    for period, factor in time_factors.items():
        print(f"  {period}: {factor}")
    print()
    print("💡 Теперь сигналы в концовке матча (75-90') будут иметь приоритет!")

if __name__ == "__main__":
    update_analyzer_with_stats()