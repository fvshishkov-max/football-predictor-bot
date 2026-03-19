@echo off
chcp 65001 >nul
title Football Bot с VPN
color 0A

echo ========================================
echo 🚀 ЗАПУСК БОТА С VPN
echo ========================================
echo.

:: Проверяем наличие xray
if not exist xray\xray.exe (
    echo ❌ Xray не найден!
    echo.
    echo Сначала установите xray: install_xray.bat
    pause
    exit /b 1
)

:: Проверяем порты
echo 🔍 Проверка портов...
netstat -ano | findstr :10808 >nul
if %errorlevel% equ 0 (
    echo ⚠️ Порт 10808 уже занят
) else (
    echo ✅ Порт 10808 свободен
)

echo.
echo 🚀 Запуск бота...
python run_fixed.py

pause