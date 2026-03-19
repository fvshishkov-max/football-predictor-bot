@echo off
chcp 1251 >nul
title Синхронизация с репозиторием
color 0A

echo ========================================
====
echo 🔄 СИНХРОНИЗАЦИЯ С РЕПОЗИТОРИЕМ
echo ========================================
====
echo.

REM ========================================
REM 1. Смотрим, что в репозитории
REM ========================================
echo 1. ФАЙЛЫ В РЕПОЗИТОРИИ (GitHub):
echo ---------------------------------
git ls-tree -r main --name-only > repo_files.txt
type repo_files.txt
echo.
echo Всего файлов в репозитории: 
find /c /v "" < repo_files.txt
echo.

REM ========================================
REM 2. Смотрим, что в локальной папке
REM ========================================
echo 2. ФАЙЛЫ В ЛОКАЛЬНОЙ ПАПКЕ:
echo ----------------------------
dir /b /s /a-d > local_files.txt
find /c /v "" < local_files.txt
echo.

REM ========================================
REM 3. Ищем файлы, которые есть в репозитории, но нет в локальной
REM ========================================
echo 3. ФАЙЛЫ ДЛЯ УДАЛЕНИЯ ИЗ РЕПОЗИТОРИЯ:
echo --------------------------------------
echo (есть в GitHub, но нет в локальной папке)
echo.

set DEL_COUNT=0
for /f "tokens=*" %%f in (repo_files.txt) do (
    if not exist "%%f" (
        if not "%%f"=="repo_files.txt" (
            if not "%%f"=="local_files.txt" (
                echo   ❌ %%f
                echo %%f>> to_delete.txt
                set /a DEL_COUNT+=1
            )
        )
    )
)

if %DEL_COUNT% equ 0 (
    echo   ✅ Лишних файлов нет
) else (
    echo.
    echo   Найдено %DEL_COUNT% файлов для удаления
)

echo.

REM ========================================
REM 4. Предложение удалить лишние файлы из репозитория
REM ========================================
if %DEL_COUNT% gtr 0 (
    echo Хотите удалить эти файлы из репозитория?
    set /p CONFIRM="Удалить (Y/N): "
    
    if /i "%CONFIRM%"=="Y" (
        echo.
        echo 4. УДАЛЕНИЕ ФАЙЛОВ ИЗ РЕПОЗИТОРИЯ:
        echo -----------------------------------
        
        for /f "tokens=*" %%f in (to_delete.txt) do (
            echo   Удаление %%f...
            git rm --cached "%%f" 2>nul
            if exist "%%f" del "%%f" 2>nul
        )
        
        echo   ✅ Готово
        echo.
        
        echo 5. СОЗДАНИЕ КОММИТА:
        echo ---------------------
        git commit -m "Remove obsolete files from repository"
        echo.
        
        echo 6. ОТПРАВКА НА GITHUB:
        echo -----------------------
        git push origin main
        echo.
    )
)

echo.
echo ========================================
====
echo ✅ ПРОВЕРКА ЗАВЕРШЕНА
echo ========================================
====

del repo_files.txt 2>nul
del local_files.txt 2>nul
del to_delete.txt 2>nul

pause