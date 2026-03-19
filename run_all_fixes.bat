@echo off
chcp 1251 >nul
title Полное исправление
color 0A

echo ========================================
====
echo 🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ PREDICTOR.PY
echo ========================================
====
echo.

echo Шаг 1: Экстренное исправление склеенных методов...
python emergency_fix_predictor.py
echo.

echo Шаг 2: Полное исправление...
python complete_fix_predictor.py
echo.

echo Шаг 3: Проверка синтаксиса...
python check_predictor.py
echo.

if %errorlevel% equ 0 (
    echo ✅ ВСЕ ИСПРАВЛЕНО!
    echo.
    echo Запустите бота: python run_fixed.py
) else (
    echo ❌ ОСТАЛИСЬ ОШИБКИ
    echo.
    echo Проверьте файл вручную
)

pause