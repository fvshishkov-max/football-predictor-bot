@echo off
chcp 1251 >nul
title Запуск с исправлением
color 0A

echo ========================================
====
echo 🔧 ЗАПУСК С ИСПРАВЛЕНИЕМ
echo ========================================
====
echo.

echo Шаг 1: Исправление predictor.py...
python fix_predictor.py
echo.

echo Шаг 2: Запуск бота...
python run_fixed.py

pause