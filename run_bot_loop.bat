@echo off
chcp 65001 >nul
title Bot Loop
color 0A

echo ========================================
echo BOT LOOP WITH RESTART
echo ========================================
echo.

:loop
echo [%time%] Starting bot...
python run_fixed.py

echo.
echo [%time%] Bot stopped. Waiting 30 seconds...
timeout /t 30 /nobreak >nul

goto loop