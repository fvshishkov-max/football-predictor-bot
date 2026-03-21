# optimize_match_analyzer.py
"""
Оптимизация match_analyzer.py на основе анализа данных
Запуск: python optimize_match_analyzer.py
"""

import re

def update_match_analyzer():
    """Обновляет match_analyzer.py с оптимизированными параметрами"""
    
    with open('match_analyzer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. ОПТИМИЗИРОВАННЫЕ ВЕСА ДЛЯ ПЕРИОДОВ (на основе анализа)
    new_time_factors = '''    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор оставшегося времени (оптимизированный на основе 74k прогнозов)"""
        if not minute:
            return 1.0
        if minute < 15:
            return 0.93   # 0-15: 34 гола, точность 0.5%
        elif minute < 30:
            return 0.91   # 15-30: 51 гол, точность 0.5%
        elif minute < 45:
            return 0.82   # 30-45: 54 гола, точность 0.5%
        elif minute < 60:
            return 0.80   # 45-60: 65 голов, точность 0.5% (максимум голов)
        elif minute < 75:
            return 0.67   # 60-75: 62 гола, точность 0.4%
        elif minute < 90:
            return 0.60   # 75-90: 51 гол, точность 0.3% (низшая точность)
        else:
            return 0.86   # 90+: 7 голов, точность 0.5%'''
    
    # Находим старый метод и заменяем
    pattern = r'def _calculate_time_factor\(self, minute: int\) -> float:.*?return [0-9.]+'
    new_content = re.sub(pattern, new_time_factors, content, flags=re.DOTALL)
    
    if new_content != content:
        with open('match_analyzer.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ match_analyzer.py обновлен с оптимизированными временными факторами")
    else:
        print("⚠️ Метод _calculate_time_factor не найден, обновление не выполнено")
    
    # 2. ОПТИМИЗИРОВАННЫЙ МИНИМАЛЬНЫЙ ПОРОГ
    with open('config.py', 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # Проверяем текущий порог
    if 'MIN_PROBABILITY_FOR_SIGNAL' in config_content:
        old_threshold = re.search(r'MIN_PROBABILITY_FOR_SIGNAL = [0-9.]+', config_content)
        if old_threshold:
            print(f"\n📊 Текущий порог: {old_threshold.group()}")
            print("💡 Рекомендуемый порог: MIN_PROBABILITY_FOR_SIGNAL = 0.52")
    
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЕ РЕКОМЕНДАЦИИ:")
    print("="*60)
    print("""
    1. ВРЕМЕННЫЕ ФАКТОРЫ (уже обновлены):
       • 0-15:   0.93  (средний)
       • 15-30:  0.91  (средний)
       • 30-45:  0.82  (выше среднего)
       • 45-60:  0.80  (высокий - пик голов)
       • 60-75:  0.67  (низкий)
       • 75-90:  0.60  (очень низкий)
       • 90+:    0.86  (выше среднего)

    2. РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ В CONFIG.PY:
       • MIN_PROBABILITY_FOR_SIGNAL = 0.52  (вместо 0.46)
       • SIGNAL_COOLDOWN = 300 (оставить)
    
    3. РЕКОМЕНДУЕМЫЕ ИСКЛЮЧЕНИЯ:
       • Исключить минуты: 85, 91, 92, 93, 94
       • Снизить вес для 75-90 периода
    
    4. ДЛЯ УЛУЧШЕНИЯ ТОЧНОСТИ:
       • Добавить проверку was_correct после каждого матча
       • Накапливать больше данных (сейчас 324 гола, нужно 1000+)
       • Увеличить порог до 52-55% для сигналов
    """)

if __name__ == "__main__":
    update_match_analyzer()