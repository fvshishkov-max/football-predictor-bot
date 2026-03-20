@echo off
chcp 1251 >nul
title Оптимизация порогов
color 0A

echo ========================================
echo 🔧 ОПТИМИЗАЦИЯ ПОРОГОВ
echo ========================================
echo.

python -c "
from signal_validator import SignalValidator
import json

v = SignalValidator()
stats = v.get_validation_stats()

print('📊 ТЕКУЩИЕ ПОРОГИ:')
print('  • Минимальная вероятность: 46%')
print('  • VERY_HIGH вес: 1.2')
print('  • HIGH вес: 1.0')
print('  • MEDIUM вес: 0.8')
print()

print('📈 РЕКОМЕНДАЦИИ:')
if stats['accuracy'] < 0.5:
    new_threshold = 48 + (50 - stats['accuracy']*100) / 10
    print(f'  • Увеличить порог до {new_threshold:.0f}%')
    
for bin_name, bin_data in stats['probability_stats'].items():
    if bin_data['total'] > 5 and bin_data.get('accuracy', 0) < 0.4:
        min_val = bin_data['min']
        print(f'  • Исключить сигналы ниже {min_val*100:.0f}% (точность {bin_data.get("accuracy",0)*100:.1f}%)')
"

echo.
pause
