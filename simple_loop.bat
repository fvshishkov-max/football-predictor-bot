@echo off
title Bot Loop

echo ========================================
echo BOT LOOP
echo ========================================
echo.

:loop
echo [%time%] Starting bot...
python run_fixed.py
echo [%time%] Bot stopped. Waiting 30 seconds...
timeout /t 30 /nobreak >nul
goto loop