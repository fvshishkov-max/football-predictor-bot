# minimal_analysis.py
# -*- coding: utf-8 -*-
from signal_validator import SignalValidator

v = SignalValidator()
s = v.get_validation_stats()

print("=" * 50)
print("СТАТИСТИКА СИГНАЛОВ")
print("=" * 50)
print(f"Всего: {s['total_signals']}")
print(f"Правильных: {s['correct']}")
print(f"Ложных: {s['false']}")
print(f"Точность: {s['accuracy']*100:.1f}%")