@echo off
chcp 1251 >nul
title Улучшенный анализ матчей
color 0A

echo ========================================
====
echo 🚀 ЗАПУСК УЛУЧШЕННОГО АНАЛИЗА МАТЧЕЙ
echo ========================================
====
echo.

REM Проверяем наличие новых файлов
echo Проверка компонентов:
echo ----------------------

if exist match_analyzer.py (
    echo [OK] match_analyzer.py
) else (
    echo [FAIL] match_analyzer.py - создайте файл
    goto :error
)

if exist predictor.py (
    echo [OK] predictor.py
) else (
    echo [FAIL] predictor.py - не найден
    goto :error
)

echo.
echo Запуск бота с улучшенным анализом...
echo.

python run_fixed.py

goto :end

:error
echo.
echo ❌ Ошибка: Не все компоненты на месте
echo.
pause
exit /b

:end
pause