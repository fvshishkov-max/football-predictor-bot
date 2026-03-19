@echo off
chcp 1251 >nul
title Обновление репозитория
color 0A

echo ========================================
echo 📦 ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ
echo ========================================
echo.

git status
echo.

git add .
echo ✅ Файлы добавлены
echo.

set /p COMMIT="Введите комментарий к коммиту: "
if "%COMMIT%"=="" set COMMIT="Update"

git commit -m "%COMMIT%"
git push origin main

echo.
echo ========================================
pause
