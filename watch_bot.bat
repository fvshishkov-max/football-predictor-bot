@echo off
chcp 65001 >nul
title Watch Bot
color 0A

echo ========================================
echo WATCHING BOT
echo ========================================
echo.

:check
cls
echo %date% %time%
echo ========================================

python -c "import json; f=open('data/predictions/predictions.json'); d=json.load(f); print(f'Predictions: {len(d.get(\"predictions\", []))}')" 2>nul
echo.

type data\logs\app.log 2>nul | find "СИГНАЛ" | tail -5

echo.
echo ========================================
timeout /t 10 /nobreak >nul
goto check