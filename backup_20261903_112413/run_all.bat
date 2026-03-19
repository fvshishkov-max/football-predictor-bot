@echo off
chcp 1251 >nul
title Полная настройка
color 0A

echo ========================================
echo 🚀 ПОЛНАЯ НАСТРОЙКА ПРОЕКТА
echo ========================================
echo.

echo Шаг 1: Организация файлов...
call organize_simple.bat
echo.

echo Шаг 2: Очистка...
call clean_simple.bat
echo.

echo Шаг 3: Проверка статуса...
call status_simple.bat
echo.

echo ========================================
echo ✅ ВСЕ ГОТОВО!
echo ========================================
echo.
echo Теперь можно запустить бота: start_bot_simple.bat
pause