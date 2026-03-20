@echo off
chcp 1251 >nul
title Синхронизация с GitHub
color 0A

echo ========================================
====
echo 🔄 СИНХРОНИЗАЦИЯ С GITHUB
echo ========================================
====
echo.

echo 1. Проверка статуса Git...
echo -------------------------
git status
echo.

echo 2. Добавление всех новых файлов...
echo -------------------------------
git add .
echo ✅ Файлы добавлены
echo.

echo 3. Статус после добавления...
echo -----------------------------
git status
echo.

echo 4. Введите комментарий к коммиту:
echo ---------------------------------
set /p COMMIT="> "

if "%COMMIT%"=="" (
    set COMMIT="Update: Sync project with GitHub %date% %time%"
)

echo.
echo 5. Создание коммита...
echo -----------------------
git commit -m "%COMMIT%"
echo.

echo 6. Отправка на GitHub...
echo -------------------------
git push origin main
echo.

echo ========================================
====
echo ✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА
echo ========================================
====
pause