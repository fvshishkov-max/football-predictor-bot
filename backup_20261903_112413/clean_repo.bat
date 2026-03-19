@echo off
chcp 1251 >nul
title Очистка репозитория
color 0A

echo ========================================
====
echo 🧹 ПОЛНАЯ ОЧИСТКА РЕПОЗИТОРИЯ
echo ========================================
====
echo.

REM ========================================
REM 1. Создаем резервную копию важных файлов
REM ========================================
echo 1. СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ:
echo -----------------------------
set BACKUP_DIR=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir %BACKUP_DIR% 2>nul

echo   Копирование важных файлов в %BACKUP_DIR%...

REM Копируем Python файлы
copy *.py %BACKUP_DIR%\ 2>nul
echo     ✅ Python файлы

REM Копируем bat файлы
copy *.bat %BACKUP_DIR%\ 2>nul
echo     ✅ Batch файлы

REM Копируем конфиги
copy config.py %BACKUP_DIR%\ 2>nul
copy .env %BACKUP_DIR%\ 2>nul 2>nul

echo   ✅ Резервная копия создана
echo.

REM ========================================
REM 2. Удаляем все из индекса Git
REM ========================================
echo 2. ОЧИСТКА GIT ИНДЕКСА:
echo ------------------------
git rm -r --cached . >nul 2>nul
echo   ✅ Индекс очищен
echo.

REM ========================================
REM 3. Добавляем только нужные файлы
REM ========================================
echo 3. ДОБАВЛЕНИЕ НУЖНЫХ ФАЙЛОВ:
echo -----------------------------

REM Python файлы
for %%f in (*.py) do (
    git add %%f
    echo   ✅ %%f
)

REM Batch файлы
for %%f in (*.bat) do (
    git add %%f
    echo   ✅ %%f
)

REM Важные конфиги
if exist .env git add .env
git add .gitignore
git add requirements.txt

REM README
if exist README.md git add README.md

echo.
echo   ✅ Все нужные файлы добавлены
echo.

REM ========================================
REM 4. Проверка статуса
REM ========================================
echo 4. ТЕКУЩИЙ СТАТУС:
echo --------------------
git status
echo.

REM ========================================
REM 5. Создание коммита
REM ========================================
set /p COMMIT="Введите комментарий к коммиту: "
if "%COMMIT%"=="" set COMMIT="Clean repository - keep only source files"

git commit -m "%COMMIT%"
echo.

REM ========================================
REM 6. Отправка на GitHub
REM ========================================
echo 5. ОТПРАВКА НА GITHUB:
echo -----------------------
git push origin main --force
echo.

echo ========================================
====
echo ✅ РЕПОЗИТОРИЙ ОЧИЩЕН
echo ========================================
====
echo.
echo Резервная копия сохранена в папке: %BACKUP_DIR%
pause