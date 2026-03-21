@echo off
chcp 65001 >nul
title Мониторинг предсказаний
color 0A

echo ========================================
echo 📊 ЗАПУСК МОНИТОРИНГА
echo ========================================
echo.

python simple_monitor.py

pause