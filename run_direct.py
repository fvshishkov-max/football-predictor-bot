# run_direct.py
"""
Прямой запуск анализа
"""

import sys
import os

# Добавляем текущую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyze_false_signals import analyze_false_signals

print("="*60)
print("🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ")
print("="*60)
print()

analyze_false_signals()

print()
print("="*60)
input("Нажмите Enter для выхода...")