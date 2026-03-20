@echo off
chcp 1251 >nul
title Анализ ложных сигналов
color 0C

echo ========================================
echo 🔍 АНАЛИЗ ЛОЖНЫХ СИГНАЛОВ
echo ========================================
echo.

python analyze_false_signals.py

echo.
pause
