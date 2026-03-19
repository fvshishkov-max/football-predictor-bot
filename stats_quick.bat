@echo off
chcp 1251 >nul
title Быстрая статистика

python -c "
import run_stats
data = run_stats.load_predictions()
if data:
    stats = run_stats.calculate_stats(data)
    if stats:
        msg = run_stats.format_stats_message(stats)
        run_stats.send_telegram_message(msg)
        print('✅ Статистика отправлена в Telegram!')
"

pause