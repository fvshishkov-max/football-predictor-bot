@echo off
chcp 65001 >nul
title Проверка синхронизации data
color 0A

echo ========================================
echo 🔍 ПРОВЕРКА СИНХРОНИЗАЦИИ DATA
echo ========================================
echo.

echo ЛОКАЛЬНЫЕ ФАЙЛЫ:
echo -----------------
if exist data (
    dir data /s /b
) else (
    echo Папка data не найдена
)

echo.
echo ФАЙЛЫ НА GITHUB:
echo -----------------
git ls-tree -r main --name-only | findstr "data/"
echo.

echo.
echo ОТЛИЧИЯ:
echo --------
echo Локальных файлов, которых нет на GitHub:
for /f "tokens=*" %%f in ('dir data /s /b 2^>nul') do (
    git ls-tree -r main --name-only | findstr /c:"%%f" >nul
    if errorlevel 1 (
        echo   ➕ %%f
    )
)

echo.
echo Файлов на GitHub, которых нет локально:
git ls-tree -r main --name-only | findstr "data/" > temp.txt
for /f "tokens=*" %%f in (temp.txt) do (
    if not exist "%%f" (
        echo   ❌ %%f
    )
)
del temp.txt 2>nul

echo.
pause