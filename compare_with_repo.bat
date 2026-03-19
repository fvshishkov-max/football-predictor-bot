@echo off
chcp 1251 >nul
title Сравнение с репозиторием
color 0A

echo ========================================
====
echo 🔍 СРАВНЕНИЕ С РЕПОЗИТОРИЕМ
echo ========================================
====
echo.

REM ========================================
REM 1. Файлы, которые есть в репозитории, но нет локально
REM ========================================
echo 1. ФАЙЛЫ ТОЛЬКО В РЕПОЗИТОРИИ:
echo --------------------------------
git ls-tree -r main --name-only > repo_temp.txt

set ONLY_IN_REPO=0
for /f "tokens=*" %%f in (repo_temp.txt) do (
    if not exist "%%f" (
        echo   ❌ %%f
        set /a ONLY_IN_REPO+=1
    )
)

if %ONLY_IN_REPO% equ 0 (
    echo   ✅ Нет лишних файлов в репозитории
)
echo.

REM ========================================
REM 2. Файлы, которые есть локально, но нет в репозитории
REM ========================================
echo 2. ФАЙЛЫ ТОЛЬКО ЛОКАЛЬНО:
echo --------------------------
dir /b /s /a-d > local_temp.txt

set ONLY_LOCAL=0
for /f "tokens=*" %%f in (local_temp.txt) do (
    git ls-files --error-unmatch "%%f" >nul 2>nul
    if errorlevel 1 (
        echo   ➕ %%f
        set /a ONLY_LOCAL+=1
    )
)

if %ONLY_LOCAL% equ 0 (
    echo   ✅ Все локальные файлы уже в репозитории
)
echo.

echo ========================================
====
echo ИТОГИ:
echo   В репозитории лишних: %ONLY_IN_REPO%
echo   Не добавлено локально: %ONLY_LOCAL%
echo ========================================
====

del repo_temp.txt 2>nul
del local_temp.txt 2>nul
pause