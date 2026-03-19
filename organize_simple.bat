@echo off
chcp 1251 >nul
title Организация проекта
color 0A

echo ========================================
echo 🔧 ОРГАНИЗАЦИЯ ПРОЕКТА
echo ========================================
echo.

echo 1. Создание папок...
mkdir data 2>nul
mkdir data\predictions 2>nul
mkdir data\history 2>nul
mkdir data\stats 2>nul
mkdir data\logs 2>nul
mkdir data\backups 2>nul
mkdir data\models 2>nul
mkdir data\cache 2>nul
mkdir archives 2>nul
echo   ✅ Папки созданы
echo.

echo 2. Перемещение файлов...

REM Файлы предсказаний
if exist predictions_history_*.csv (
    echo   Перемещение predictions_history_*.csv...
    move predictions_history_*.csv data\history\ 2>nul
)
if exist signals_history_*.csv (
    echo   Перемещение signals_history_*.csv...
    move signals_history_*.csv data\history\ 2>nul
)
if exist predictions_stats_*.txt (
    echo   Перемещение predictions_stats_*.txt...
    move predictions_stats_*.txt data\stats\ 2>nul
)

REM Основные файлы
if exist predictions.json (
    echo   Перемещение predictions.json...
    move predictions.json data\predictions\ 2>nul
)
if exist prediction_stats.json (
    echo   Перемещение prediction_stats.json...
    move prediction_stats.json data\stats\ 2>nul
)
if exist xgboost_model.pkl (
    echo   Перемещение xgboost_model.pkl...
    move xgboost_model.pkl data\models\ 2>nul
)

REM Базы данных
if exist matches_history.db (
    echo   Перемещение matches_history.db...
    move matches_history.db data\history\ 2>nul
)
if exist football_cache.db (
    echo   Перемещение football_cache.db...
    move football_cache.db data\cache\ 2>nul
)

REM Логи
if exist *.log (
    echo   Перемещение логов...
    move *.log data\logs\ 2>nul
)

echo   ✅ Файлы перемещены
echo.

echo 3. Очистка временных файлов...
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo   ✅ Временные файлы удалены
echo.

echo 4. Результат:
echo --------------------------------
if exist data (
    dir data /s /b
) else (
    echo Папка data не найдена
)

echo.
echo ========================================
echo ✅ ГОТОВО!
echo ========================================
pause