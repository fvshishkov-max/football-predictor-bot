@echo off
chcp 1251 >nul
title Запуск статистики

python tools/run_stats.py
pause
