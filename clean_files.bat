@echo off
chcp 65001 >nul
title Очистка проекта
color 0A

echo ========================================
echo 🧹 ОЧИСТКА ПРОЕКТА
echo ========================================
echo.

echo 1. Удаление временных файлов Python...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   ✅ Временные файлы удалены
echo.

echo 2. Удаление логов...
del /s /q *.log 2>nul
del /s /q *.log.* 2>nul
del /s /q *.backup 2>nul
del /s /q *.back 2>nul
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul
echo   ✅ Логи удалены
echo.

echo 3. Удаление тестовых файлов (кроме test_telegram.py)...
for %%f in (debug_*.py diagnose_*.py test_*.py) do (
    if not "%%f"=="test_telegram.py" (
        del /s /q %%f 2>nul
    )
)
echo   ✅ Тестовые файлы удалены
echo.

echo 4. Проверка папки xray...
if exist xray (
    echo   📁 Папка xray найдена
    echo   ❓ Удалить папку xray? (Y/N)
    set /p answer=
    if /i "!answer!"=="Y" (
        rmdir /s /q xray
        echo   ✅ Папка xray удалена
    ) else (
        echo   ⏹ Папка xray сохранена
    )
) else (
    echo   📁 Папка xray не найдена
)

echo.
echo ========================================
echo ✅ Очистка завершена!
echo ========================================
pause