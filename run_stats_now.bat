@echo off
chcp 1251 >nul
title Статистика прогнозов
color 0A

echo ========================================
====
echo 📊 ОТПРАВКА СТАТИСТИКИ В TELEGRAM
echo ========================================
====
echo.

echo Отправка отчета...
python -c "
import run_stats
data = run_stats.load_predictions()
if data:
    stats = run_stats.calculate_stats(data)
    if stats:
        msg = run_stats.format_stats_message(stats)
        run_stats.send_telegram_message(msg)
        print('✅ Отчет отправлен!')
"

echo.
pause