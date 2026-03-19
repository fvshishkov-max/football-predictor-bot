@echo off
chcp 65001 >nul
title Очистка временных файлов
color 0A

echo ========================================
echo 🧹 ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ
echo ========================================
echo.

echo 1. Удаление Python cache...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo ✅ Python cache удален
echo.

echo 2. Удаление временных файлов...
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul
echo ✅ Временные файлы удалены
echo.

echo ========================================
echo ✅ ОЧИСТКА ЗАВЕРШЕНА
echo ========================================
pause