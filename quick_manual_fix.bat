@echo off
chcp 1251 >nul
title Ручное исправление
color 0A

echo ========================================
====
echo 📝 РУЧНОЕ ИСПРАВЛЕНИЕ PREDICTOR.PY
echo ========================================
====
echo.

echo Открываем predictor.py в блокноте...
notepad predictor.py

echo.
echo После исправления закройте блокнот и нажмите любую клавишу
pause >nul

echo.
echo Проверка исправления...
python check_predictor.py

pause