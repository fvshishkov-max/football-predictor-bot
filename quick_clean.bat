@echo off
chcp 65001 >nul
title Быстрая очистка проекта
color 0A

echo ========================================
echo 🧹 БЫСТРАЯ ОЧИСТКА ПРОЕКТА
echo ========================================
echo.

echo Удаление временных файлов Python...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
rmdir /s /q __pycache__ 2>nul

echo Удаление логов...
del /s /q *.log 2>nul
del /s /q *.log.* 2>nul
del /s /q *.backup 2>nul
del /s /q *.back 2>nul
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul

echo Удаление тестовых файлов (кроме test_telegram.py)...
dir /b /s test_*.py | findstr /v "test_telegram.py" > temp.txt
for /f "tokens=*" %%f in (temp.txt) do del "%%f" 2>nul
del temp.txt 2>nul

echo Удаление диагностических файлов...
del /s /q debug_*.py 2>nul
del /s /q diagnose_*.py 2>nul

echo.
echo ========================================
echo ✅ Очистка завершена!
echo ========================================
pause