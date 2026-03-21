@echo off
chcp 65001 >nul
title Синхронизация папки data
color 0A

echo ========================================
echo 📁 СИНХРОНИЗАЦИЯ ПАПКИ DATA С GITHUB
echo ========================================
echo.

echo 1. Проверка содержимого локальной папки data...
echo -----------------------------------------------
if exist data (
    echo 📂 Содержимое папки data:
    dir data /s
    echo.
    
    echo 📊 Статистика файлов:
    for /f %%i in ('dir data /s /b ^| find /c /v ""') do set count=%%i
    echo   Всего файлов: %count%
    
    for /f %%i in ('dir data /s /b ^| findstr /i ".json" ^| find /c /v ""') do set json_count=%%i
    echo   JSON файлов: %json_count%
    
    for /f %%i in ('dir data /s /b ^| findstr /i ".db" ^| find /c /v ""') do set db_count=%%i
    echo   DB файлов: %db_count%
) else (
    echo ❌ Папка data не найдена!
    pause
    exit /b
)

echo.
echo 2. Временное удаление правил игнорирования data из .gitignore...
echo -----------------------------------------------------------------
rem Создаем резервную копию .gitignore
copy .gitignore .gitignore.backup

rem Создаем временный .gitignore без правил для data
findstr /v "data/" .gitignore > .gitignore.temp
move .gitignore.temp .gitignore
echo ✅ .gitignore временно изменен
echo.

echo 3. Добавление файлов data в Git...
echo ----------------------------------
git add data/
echo ✅ Файлы добавлены
echo.

echo 4. Статус после добавления...
echo -----------------------------
git status
echo.

echo 5. Создание коммита...
echo -----------------------
set /p "COMMIT=Введите комментарий для коммита: "
if "%COMMIT%"=="" set COMMIT=Add: Sync data folder with actual files

git commit -m "%COMMIT%"
echo.

echo 6. Отправка на GitHub...
echo -------------------------
git push origin main
echo.

echo 7. Восстановление исходного .gitignore...
echo -----------------------------------------
move .gitignore.backup .gitignore
echo ✅ .gitignore восстановлен
echo.

echo ========================================
echo ✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА
echo ========================================
echo.
echo 📁 Файлы data загружены на GitHub:
git ls-tree -r main --name-only | findstr "data/"
echo.
pause