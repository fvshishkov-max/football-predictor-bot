@echo off
chcp 1251 >nul
title Полная проверка и очистка
color 0A

echo ========================================
echo 🔍 ПОЛНАЯ ПРОВЕРКА ПРОЕКТА
echo ========================================
echo.

REM ========================================
REM 1. Проверка структуры папок
REM ========================================
echo 1. ПРОВЕРКА ПАПОК:
echo -------------------
set MISSING_FOLDERS=0

call :check_folder data
call :check_folder data\predictions
call :check_folder data\history
call :check_folder data\stats
call :check_folder data\logs
call :check_folder data\backups
call :check_folder data\models
call :check_folder data\cache

if %MISSING_FOLDERS% equ 0 (
    echo   ✅ Все папки на месте
) else (
    echo   ⚠️ Отсутствует %MISSING_FOLDERS% папок
)
echo.

REM ========================================
REM 2. Проверка основных файлов
REM ========================================
echo 2. ПРОВЕРКА ФАЙЛОВ:
echo -------------------
set MISSING_FILES=0

call :check_file run_fixed.py
call :check_file app.py
call :check_file predictor.py
call :check_file telegram_bot.py
call :check_file stats_reporter.py
call :check_file translations.py
call :check_file api_client.py
call :check_file models.py
call :check_file config.py
call :check_file team_form.py
call :check_file betting_optimizer.py
call :check_file feature_engineering.py
call :check_file statistical_models.py
call :check_file advanced_features.py

if %MISSING_FILES% equ 0 (
    echo   ✅ Все файлы на месте
) else (
    echo   ⚠️ Отсутствует %MISSING_FILES% файлов
)
echo.

REM ========================================
REM 3. Поиск лишних файлов
REM ========================================
echo 3. ПОИСК ЛИШНИХ ФАЙЛОВ:
echo ------------------------

echo   Временные файлы Python:
set TEMP_COUNT=0
for /r %%i in (*.pyc) do set /a TEMP_COUNT+=1
if %TEMP_COUNT% gtr 0 (
    echo     ⚠️ Найдено %TEMP_COUNT% .pyc файлов
) else (
    echo     ✅ .pyc файлов нет
)

echo   Папки __pycache__:
set CACHE_COUNT=0
for /d /r %%i in (__pycache__) do set /a CACHE_COUNT+=1
if %CACHE_COUNT% gtr 0 (
    echo     ⚠️ Найдено %CACHE_COUNT% папок __pycache__
) else (
    echo     ✅ Папок __pycache__ нет
)

echo   Лог файлы в корне:
set LOG_COUNT=0
for %%i in (*.log) do set /a LOG_COUNT+=1
if %LOG_COUNT% gtr 0 (
    echo     ⚠️ Найдено %LOG_COUNT% лог-файлов в корне
) else (
    echo     ✅ Лог-файлов в корне нет
)

echo   Бэкап файлы:
set BACKUP_COUNT=0
for %%i in (*.backup *.back) do set /a BACKUP_COUNT+=1
if %BACKUP_COUNT% gtr 0 (
    echo     ⚠️ Найдено %BACKUP_COUNT% бэкап-файлов
) else (
    echo     ✅ Бэкап-файлов нет
)

echo   CSV файлы истории:
set CSV_COUNT=0
for %%i in (predictions_history_*.csv signals_history_*.csv) do set /a CSV_COUNT+=1
if %CSV_COUNT% gtr 0 (
    echo     ⚠️ Найдено %CSV_COUNT% CSV файлов в корне
) else (
    echo     ✅ CSV файлов в корне нет
)

echo   Текстовые файлы статистики:
set TXT_COUNT=0
for %%i in (predictions_stats_*.txt) do set /a TXT_COUNT+=1
if %TXT_COUNT% gtr 0 (
    echo     ⚠️ Найдено %TXT_COUNT% TXT файлов в корне
) else (
    echo     ✅ TXT файлов в корне нет
)
echo.

REM ========================================
REM 4. Подсчет файлов в папках
REM ========================================
echo 4. СТАТИСТИКА ФАЙЛОВ:
echo ----------------------

if exist data (
    echo   Папка data:
    for /d %%i in (data\*) do (
        set COUNT=0
        for %%j in (%%i\*) do set /a COUNT+=1
        call :show_count "%%i" %COUNT%
    )
) else (
    echo   ❌ Папка data не найдена
)
echo.

REM ========================================
REM 5. Предложение удалить лишнее
REM ========================================
set /p DELETE="Удалить все временные и лишние файлы? (Y/N): "

if /i "%DELETE%"=="Y" (
    echo.
    echo 5. УДАЛЕНИЕ ЛИШНИХ ФАЙЛОВ:
    echo ---------------------------
    
    echo   Удаление .pyc файлов...
    del /s /q *.pyc 2>nul
    echo     ✅ Готово
    
    echo   Удаление папок __pycache__...
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
    echo     ✅ Готово
    
    echo   Удаление лог-файлов из корня...
    del *.log 2>nul
    echo     ✅ Готово
    
    echo   Удаление бэкап-файлов...
    del *.backup 2>nul
    del *.back 2>nul
    echo     ✅ Готово
    
    echo   Перемещение CSV файлов в data\history...
    move predictions_history_*.csv data\history\ 2>nul
    move signals_history_*.csv data\history\ 2>nul
    echo     ✅ Готово
    
    echo   Перемещение TXT файлов в data\stats...
    move predictions_stats_*.txt data\stats\ 2>nul
    echo     ✅ Готово
    
    echo   ✅ Очистка завершена
)

echo.
echo ========================================
echo ✅ ПРОВЕРКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Теперь можно обновить репозиторий: git_update.bat
pause
goto :eof

:check_folder
if exist %1 (
    echo   ✅ %1
) else (
    echo   ❌ %1
    set /a MISSING_FOLDERS+=1
)
goto :eof

:check_file
if exist %1 (
    echo   ✅ %1
) else (
    echo   ❌ %1
    set /a MISSING_FILES+=1
)
goto :eof

:show_count
set FOLDER=%~1
set FOLDER_NAME=%~nx1
set COUNT=%~2
if %COUNT% gtr 0 (
    echo     📁 %FOLDER_NAME%: %COUNT% файлов
) else (
    echo     📁 %FOLDER_NAME%: пусто
)
goto :eof