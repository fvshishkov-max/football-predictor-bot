@echo off
echo ========================================
echo СИНХРОНИЗАЦИЯ DATA С GITHUB
echo ========================================
echo.

echo Выберите действие:
echo 1 - Проверить содержимое
echo 2 - Синхронизировать только структуру (.gitkeep)
echo 3 - Синхронизировать все данные
echo.

set /p choice="Выбор (1-3): "

if "%choice%"=="1" (
    python check_data.py
)
if "%choice%"=="2" (
    python sync_only_structure.py
)
if "%choice%"=="3" (
    python sync_data.py
)

pause