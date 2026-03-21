@echo off
chcp 65001 >nul
title Синхронизация данных
color 0A

echo ========================================
echo 📁 СИНХРОНИЗАЦИЯ ТОЛЬКО ФАЙЛОВ DATA
echo ========================================
echo.

echo 1. Принудительное добавление файлов data...
echo -------------------------------------------
git add data/ -f
echo ✅ Файлы добавлены (--force)
echo.

echo 2. Статус добавленных файлов...
echo -------------------------------
git status
echo.

echo 3. Создание коммита...
echo -----------------------
set /p "COMMIT=Введите комментарий: "
if "%COMMIT%"=="" set COMMIT=Update: Data files sync

git commit -m "%COMMIT%"
echo.

echo 4. Отправка на GitHub...
echo -------------------------
git push origin main
echo.

echo ========================================
echo ✅ ГОТОВО
echo ========================================
pause