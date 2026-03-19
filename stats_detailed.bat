@echo off
chcp 1251 >nul
title Меню статистики
color 0A

:menu
cls
echo ========================================
====
echo 📊 МЕНЮ СТАТИСТИКИ
echo ========================================
====
echo.
echo [1] Общая статистика (с подтверждением)
echo [2] Общая статистика (сразу в Telegram)
echo [3] Статистика за сегодня
echo [4] Статистика за вчера
echo [5] Статистика за указанную дату
echo [6] Выход
echo.

set /p choice="Выберите пункт (1-6): "

if "%choice%"=="1" goto stats_normal
if "%choice%"=="2" goto stats_now
if "%choice%"=="3" goto stats_today
if "%choice%"=="4" goto stats_yesterday
if "%choice%"=="5" goto stats_date
if "%choice%"=="6" exit

echo Неверный выбор!
pause
goto menu

:stats_normal
python run_stats.py
pause
goto menu

:stats_now
python run_stats_now.bat
pause
goto menu

:stats_today
python -c "
from datetime import datetime
import run_stats, stats_by_date
today = datetime.now().strftime('%%Y-%%m-%%d')
stats = stats_by_date.get_stats_by_date(today)
if stats and stats['total'] > 0:
    print(f'\n📊 Статистика за {today}')
    print(f'Прогнозов: {stats[''total'']}')
    print(f'Совпало: {stats[''correct'']}')
    print(f'Точность: {stats[''accuracy'']:.1f}%%')
    send = input('\nОтправить в Telegram? (y/n): ')
    if send.lower() == 'y':
        lines = [f'📊 **Статистика за {today}**', f'Прогнозов: {stats[''total'']}', 
                f'Совпало: {stats[''correct'']}', f'Точность: {stats[''accuracy'']:.1f}%%']
        run_stats.send_telegram_message('\n'.join(lines))
else:
    print('❌ Нет прогнозов за сегодня')
"
pause
goto menu

:stats_yesterday
python -c "
from datetime import datetime, timedelta
import run_stats, stats_by_date
yesterday = (datetime.now() - timedelta(1)).strftime('%%Y-%%m-%%d')
stats = stats_by_date.get_stats_by_date(yesterday)
if stats and stats['total'] > 0:
    print(f'\n📊 Статистика за {yesterday}')
    print(f'Прогнозов: {stats[''total'']}')
    print(f'Совпало: {stats[''correct'']}')
    print(f'Точность: {stats[''accuracy'']:.1f}%%')
    send = input('\nОтправить в Telegram? (y/n): ')
    if send.lower() == 'y':
        lines = [f'📊 **Статистика за {yesterday}**', f'Прогнозов: {stats[''total'']}', 
                f'Совпало: {stats[''correct'']}', f'Точность: {stats[''accuracy'']:.1f}%%']
        run_stats.send_telegram_message('\n'.join(lines))
else:
    print('❌ Нет прогнозов за вчера')
"
pause
goto menu

:stats_date
set /p user_date="Введите дату (ГГГГ-ММ-ДД): "
python stats_by_date.py %user_date%
pause
goto menu