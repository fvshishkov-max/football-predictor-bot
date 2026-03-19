@echo off
chcp 1251 >nul
title Диагностика статистики
color 0A

echo ========================================
====
echo 🔍 ДИАГНОСТИКА СТАТИСТИКИ
echo ========================================
====
echo.

echo 1. Проверка файла с предсказаниями...
python check_predictions_file.py
echo.

echo 2. Просмотр последних предсказаний...
python show_predictions.py
echo.

echo 3. Исправление формата дат...
python fix_predictions_format.py
echo.

echo 4. Проверка статистики за сегодня...
python stats_by_date.py %date:~-4,4%-%date:~-10,2%-%date:~-7,2%
echo.

echo 5. Проверка общей статистики...
python run_stats.py
echo.

echo ========================================
====
pause