@echo off
chcp 1251 >nul
title Восстановление папок
color 0A

echo ========================================
====
echo 🔧 ВОССТАНОВЛЕНИЕ ПАПОК
echo ========================================
====
echo.

REM ========================================
REM 1. Создаем нужные папки локально
REM ========================================
echo 1. СОЗДАНИЕ ЛОКАЛЬНЫХ ПАПОК:
echo -----------------------------

mkdir data 2>nul
mkdir data\predictions 2>nul
mkdir data\history 2>nul
mkdir data\stats 2>nul
mkdir data\logs 2>nul
mkdir data\backups 2>nul
mkdir data\models 2>nul
mkdir data\cache 2>nul
mkdir archives 2>nul

echo   ✅ Все папки созданы
echo.

REM ========================================
REM 2. Создаем .gitkeep файлы
REM ========================================
echo 2. СОЗДАНИЕ .GITKEEP ФАЙЛОВ:
echo ----------------------------

echo. > data\.gitkeep 2>nul
echo. > data\predictions\.gitkeep 2>nul
echo. > data\history\.gitkeep 2>nul
echo. > data\stats\.gitkeep 2>nul
echo. > data\logs\.gitkeep 2>nul
echo. > data\backups\.gitkeep 2>nul
echo. > data\models\.gitkeep 2>nul
echo. > data\cache\.gitkeep 2>nul
echo. > archives\.gitkeep 2>nul

echo   ✅ .gitkeep файлы созданы
echo.

REM ========================================
REM 3. Добавляем в Git
REM ========================================
echo 3. ДОБАВЛЕНИЕ В GIT:
echo ---------------------

git add data\.gitkeep
git add data\predictions\.gitkeep
git add data\history\.gitkeep
git add data\stats\.gitkeep
git add data\logs\.gitkeep
git add data\backups\.gitkeep
git add data\models\.gitkeep
git add data\cache\.gitkeep
git add archives\.gitkeep

echo   ✅ Файлы добавлены в Git
echo.

REM ========================================
REM 4. Проверка статуса
REM ========================================
echo 4. ТЕКУЩИЙ СТАТУС:
echo -------------------
git status
echo.

REM ========================================
REM 5. Создание коммита
REM ========================================
set /p COMMIT="Введите комментарий для восстановления папок: "
if "%COMMIT%"=="" set COMMIT="Restore project folders with .gitkeep"

git commit -m "%COMMIT%"
echo.

REM ========================================
REM 6. Отправка на GitHub
REM ========================================
echo 5. ОТПРАВКА НА GITHUB:
echo -----------------------
git push origin main
echo.

echo ========================================
====
echo ✅ ПАПКИ ВОССТАНОВЛЕНЫ
echo ========================================
====
pause