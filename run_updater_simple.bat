@echo off
chcp 65001 >nul
title Update Scheduler
color 0A

echo ========================================
echo STARTING UPDATE SCHEDULER
echo ========================================
echo.

python simple_updater_no_emoji.py

pause