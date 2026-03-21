@echo off
chcp 65001 >nul
title Live Monitor
color 0A

echo ========================================
echo LIVE BOT MONITOR
echo ========================================
echo.

:loop
cls
echo %date% %time%
echo ========================================
echo.

python check_predictions_count.py

echo.
echo ========================================
echo Last log lines:
type data\logs\app.log 2>nul | find "СИГНАЛ" | tail -5

timeout /t 30 /nobreak >nul
goto loop