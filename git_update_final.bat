@echo off
chcp 1251 >nul
title Обновление GitHub
color 0A

echo ========================================
echo 📦 ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ
echo ========================================
echo.

REM Проверяем, не забыли ли мы запустить очистку
if exist *.pyc (
    echo ⚠️ ВНИМАНИЕ: Найдены временные файлы!
    echo    Сначала запустите full_cleanup.bat
    echo.
    set /p CONTINUE="Все равно продолжить? (Y/N): "
    if /i not "!CONTINUE!"=="Y" exit /b
)

echo 1. Текущий статус Git:
echo -----------------------
git status
echo.

echo 2. Добавление файлов...
git add .
echo   ✅ Готово
echo.

echo 3. Статус после добавления:
git status
echo.

echo 4. Введите комментарий к коммиту:
set /p COMMIT="> "

if "%COMMIT%"=="" (
    set COMMIT="Project cleanup and organization %date%"
)

echo.
echo 5. Создание коммита...
git commit -m "%COMMIT%"
echo.

echo 6. Отправка на GitHub...
git push origin main
echo.

echo ========================================
echo ✅ РЕПОЗИТОРИЙ ОБНОВЛЕН
echo ========================================
pause