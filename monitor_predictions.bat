@echo off
chcp 65001 >nul
title Мониторинг предсказаний
color 0A

echo ========================================
echo 📊 МОНИТОРИНГ ПРЕДСКАЗАНИЙ
echo ========================================
echo.

:loop
cls
echo ========================================
echo %date% %time%
echo ========================================
echo.

python view_predictions.py

echo.
echo ========================================
echo Обновление через 30 секунд...
timeout /t 30 /nobreak >nul
goto loop