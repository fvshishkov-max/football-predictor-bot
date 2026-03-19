@echo off
chcp 1251 >nul
title Статистика прогнозов
color 0A

echo ========================================
====
echo 📊 ЗАПУСК СТАТИСТИКИ ПРОГНОЗОВ
echo ========================================
====
echo.

python run_stats.py

echo.
pause