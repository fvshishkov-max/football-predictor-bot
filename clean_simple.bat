@echo off
chcp 1251 >nul
title Очистка проекта
color 0A

echo ========================================
echo 🧹 ОЧИСТКА ПРОЕКТА
echo ========================================
echo.

echo 1. Удаление Python cache...
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   ✅ Готово
echo.

echo 2. Удаление логов...
del /s /q *.log 2>nul
echo   ✅ Готово
echo.

echo 3. Удаление временных файлов...
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul
del /s /q *.backup 2>nul
del /s /q *.back 2>nul
echo   ✅ Готово
echo.

echo ========================================
echo ✅ ОЧИСТКА ЗАВЕРШЕНА
echo ========================================
pause