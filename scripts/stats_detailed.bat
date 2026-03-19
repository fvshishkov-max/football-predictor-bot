@echo off
chcp 1251 >nul
title Меню статистики
color 0A

:menu
cls
echo ========================================
echo 📊 МЕНЮ СТАТИСТИКИ
echo ========================================
echo.
echo [1] Общая статистика
echo [2] Статистика за сегодня
echo [3] Статистика за вчера
echo [4] Статистика за указанную дату
echo [5] Диагностика
echo [6] Выход
echo.

set /p choice="Выберите пункт (1-6): "

if "%choice%"=="1" goto stats_all
if "%choice%"=="2" goto stats_today
if "%choice%"=="3" goto stats_yesterday
if "%choice%"=="4" goto stats_date
if "%choice%"=="5" goto diagnose
if "%choice%"=="6" exit

echo Неверный выбор!
pause
goto menu

:stats_all
python tools/run_stats.py
pause
goto menu

:stats_today
python tools/stats_by_date.py %date:~-4,4%-%date:~-10,2%-%date:~-7,2%
pause
goto menu

:stats_yesterday
python -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(1)).strftime('%%Y-%%m-%%d'))" > temp.txt
set /p YDATE=<temp.txt
del temp.txt
python tools/stats_by_date.py %YDATE%
pause
goto menu

:stats_date
set /p user_date="Введите дату (ГГГГ-ММ-ДД): "
python tools/stats_by_date.py %user_date%
pause
goto menu

:diagnose
call scripts\diagnose_stats.bat
pause
goto menu
