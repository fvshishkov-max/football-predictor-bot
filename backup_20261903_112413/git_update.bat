@echo off
chcp 65001 >nul
title Обновление GitHub
color 0A

echo ========================================
echo 📦 ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ
echo ========================================
echo.

echo 1. Проверка статуса...
git status

echo.
echo 2. Добавление файлов...
git add .

echo.
echo 3. Статус после добавления:
git status

echo.
echo 4. Введите комментарий к коммиту:
set /p commit_message="> "

if "%commit_message%"=="" (
    set commit_message=Update %date% %time%
)

echo.
echo 5. Создание коммита...
git commit -m "%commit_message%"

echo.
echo 6. Отправка на GitHub...
git push origin main

echo.
echo ========================================
echo ✅ Репозиторий обновлен!
echo ========================================
pause