@echo off
chcp 65001 >nul
title Fix and Restart
color 0A

echo ========================================
echo FIXING CONFIG AND RESTARTING
echo ========================================
echo.

echo 1. Killing old bot process...
taskkill /f /im python.exe 2>nul
echo Done.

echo.
echo 2. Fixing config.py...
echo.

echo 3. Starting bot...
python run_fixed.py

pause