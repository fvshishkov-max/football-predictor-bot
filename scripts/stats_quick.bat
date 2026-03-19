@echo off
chcp 1251 >nul
title Быстрая статистика

python tools/run_stats.py
pause
