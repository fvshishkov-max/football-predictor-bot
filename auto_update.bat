@echo off
chcp 65001 >nul
title Автообновление результатов
color 0A

echo ========================================
echo ⚽ АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ
echo ========================================
echo.

python auto_update_results.py

echo.
pause