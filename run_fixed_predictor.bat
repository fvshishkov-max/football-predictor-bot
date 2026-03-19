@echo off
chcp 1251 >nul
title Исправление predictor.py
color 0A

echo ========================================
====
echo 🔧 ИСПРАВЛЕНИЕ PREDICTOR.PY
echo ========================================
====
echo.

echo 1. Поиск проблемы...
python debug_predictor.py
echo.

echo 2. Попытка автоматического исправления...
python fix_indentation.py
echo.

echo 3. Проверка исправления...
python check_predictor.py
echo.

if %errorlevel% equ 0 (
    echo ✅ Файл успешно исправлен!
    echo.
    echo Запустите бота: python run_fixed.py
) else (
    echo ❌ Остались ошибки. Нужно ручное исправление.
    echo.
    echo Откройте predictor.py и найдите строки 636-637
    echo Замените проблемный метод на код из manual_fix.txt
)

echo.
pause