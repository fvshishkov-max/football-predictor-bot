@echo off
chcp 65001 >nul
title Monitor
color 0A

echo ========================================
echo STARTING MONITOR
echo ========================================
echo.

python simple_monitor_no_emoji.py

pause