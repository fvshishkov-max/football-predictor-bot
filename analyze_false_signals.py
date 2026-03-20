# -*- coding: utf-8 -*-
from signal_validator import SignalValidator

def analyze_false_signals():
    validator = SignalValidator()
    stats = validator.get_validation_stats()

    print("=" * 60)
    print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
    print("=" * 60)

    print("
📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего сигналов: {stats['total_signals']}")
    print(f"  ✅ Правильных: {stats['correct']}")
    print(f"  ❌ Ложных: {stats['false']}")
    print(f"  🎯 Точность: {stats['accuracy'] * 100:.1f}%")

    if stats['recent_false']:
        print("
📋 ПОСЛЕДНИЕ ЛОЖНЫЕ СИГНАЛЫ:")
        for false in stats['recent_false'][-5:]:
            print(f"  • {false['home']} vs {false['away']} - {false['probability']*100:.1f}% ({false['confidence']}) на {false['minute']}'")

if __name__ == "__main__":
    analyze_false_signals()
