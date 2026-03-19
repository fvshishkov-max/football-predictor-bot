@echo off
chcp 1251 >nul
title Быстрый старт
color 0A

echo ========================================
====
echo 🚀 БЫСТРЫЙ СТАРТ ВСЕХ КОМПОНЕНТОВ
echo ========================================
====
echo.

:menu
echo Выберите действие:
echo.
echo [1] Запустить тест анализатора
echo [2] Запустить бота с улучшенным анализом
echo [3] Анализ эффективности фильтров
echo [4] Выход
echo.

set /p choice="Ваш выбор (1-4): "

if "%choice%"=="1" goto :test
if "%choice%"=="2" goto :bot
if "%choice%"=="3" goto :analyze
if "%choice%"=="4" exit

echo Неверный выбор!
goto :menu

:test
echo.
echo Запуск теста анализатора...
python test_analyzer.py
echo.
pause
goto :menu

:bot
echo.
echo Запуск бота...
python run_fixed.py
pause
goto :menu

:analyze
echo.
echo Анализ эффективности фильтров...
python analyze_filters.py
echo.
pause
goto :menu