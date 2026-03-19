@echo off
chcp 1251 >nul
title Обновление репозитория
color 0A

echo ========================================
====
echo 📦 ПОЛНОЕ ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ
echo ========================================
====
echo.

echo 1. Проверка статуса Git...
git status
echo.

echo 2. Добавление всех новых файлов...
git add .
echo ✅ Файлы добавлены
echo.

echo 3. Статус после добавления:
git status
echo.

echo 4. Введите комментарий к коммиту:
set /p COMMIT="> "

if "%COMMIT%"=="" (
    set COMMIT="Update: Add statistics tools and match analyzer"
)

echo.
echo 5. Создание коммита...
git commit -m "%COMMIT%"
echo.

echo 6. Отправка на GitHub...
git push origin main
echo.

echo ========================================
====
echo ✅ РЕПОЗИТОРИЙ ОБНОВЛЕН
echo ========================================
====
pause