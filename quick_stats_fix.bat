@echo off
chcp 1251 >nul
title Быстрое исправление статистики
color 0A

echo ========================================
====
echo 🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ СТАТИСТИКИ
echo ========================================
====
echo.

echo 1. Добавление тестовых результатов...
python fix_missing_results.py
echo.

echo 2. Проверка статистики за сегодня...
python stats_by_date.py %date:~-4,4%-%date:~-10,2%-%date:~-7,2%
echo.

echo 3. Проверка общей статистики...
python run_stats.py
echo.

echo ========================================
====
pause