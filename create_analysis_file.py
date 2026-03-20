# create_analysis_file.py
"""
Создает правильно закодированный файл analyze_false_signals.py
"""

content = '''# -*- coding: utf-8 -*-
from signal_validator import SignalValidator

def analyze_false_signals():
    validator = SignalValidator()
    stats = validator.get_validation_stats()

    print("=" * 60)
    print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
    print("=" * 60)

    print("\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего сигналов: {stats['total_signals']}")
    print(f"  ✅ Правильных: {stats['correct']}")
    print(f"  ❌ Ложных: {stats['false']}")
    print(f"  🎯 Точность: {stats['accuracy'] * 100:.1f}%")

    if stats['recent_false']:
        print("\n📋 ПОСЛЕДНИЕ ЛОЖНЫЕ СИГНАЛЫ:")
        for false in stats['recent_false'][-5:]:
            print(f"  • {false['home']} vs {false['away']} - {false['probability']*100:.1f}% ({false['confidence']}) на {false['minute']}'")

if __name__ == "__main__":
    analyze_false_signals()
'''

with open('analyze_false_signals.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл analyze_false_signals.py успешно создан с правильной кодировкой!")