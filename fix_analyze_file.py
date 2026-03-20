# fix_analyze_file.py
"""
Принудительное исправление файла analyze_false_signals.py
"""

import os

def fix_file():
    """Перезаписывает файл с правильным содержимым"""
    
    content = '''"""
analyze_false_signals.py - Анализ ложных сигналов для улучшения фильтрации
"""

import json
from signal_validator import SignalValidator

def analyze_false_signals():
    """Анализирует ложные сигналы и предлагает улучшения"""
    
    validator = SignalValidator()
    stats = validator.get_validation_stats()
    
    print("=" * 60)
    print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
    print("=" * 60)
    
    print("\n📊 Общая статистика:")
    print(f"  Всего сигналов: {stats['total_signals']}")
    print(f"  ✅ Правильных: {stats['correct']}")
    print(f"  ❌ Ложных: {stats['false']}")
    print(f"  🎯 Точность: {stats['accuracy'] * 100:.1f}%")
    
    if stats['recent_false']:
        print("\n📋 Последние ложные сигналы:")
        for false in stats['recent_false'][-5:]:
            print(f"  • {false['home']} vs {false['away']} - {false['probability'] * 100:.1f}% ({false['confidence']}) на {false['minute']}'")
    
    print("\n📊 Статистика по вероятности:")
    for bin_name, bin_data in stats['probability_stats'].items():
        if bin_data['total'] > 0:
            acc = bin_data.get('accuracy', 0) * 100
            print(f"  {bin_name}: {bin_data['total']} сигналов, точность {acc:.1f}%")
    
    print("\n📊 Статистика по минутам:")
    for minute, minute_stats in sorted(stats['minute_stats'].items()):
        if minute_stats['total'] > 0:
            acc = minute_stats['accuracy'] * 100
            print(f"  {minute}-{minute + 9} мин: {minute_stats['total']} сигналов, точность {acc:.1f}%")
    
    print("\n" + "=" * 60)
    print("💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
    print("=" * 60)
    
    for bin_name, bin_data in stats['probability_stats'].items():
        if bin_data['total'] > 5 and bin_data.get('accuracy', 0) < 0.4:
            print(f"  • Повысить порог для диапазона {bin_name} (сейчас {bin_data['accuracy'] * 100:.1f}%)")
    
    for minute, minute_stats in sorted(stats['minute_stats'].items()):
        if minute_stats['total'] > 5 and minute_stats['accuracy'] < 0.35:
            print(f"  • Исключить минуты {minute}-{minute + 9} (точность {minute_stats['accuracy'] * 100:.1f}%)")
    
    if stats['accuracy'] < 0.5:
        print(f"  • Общая точность низкая ({stats['accuracy'] * 100:.1f}%) - увеличьте порог до 48-50%")

if __name__ == "__main__":
    analyze_false_signals()
'''
    
    with open('analyze_false_signals.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл analyze_false_signals.py успешно перезаписан!")
    print("\nТеперь запустите анализ:")

if __name__ == "__main__":
    fix_file()