@echo off
chcp 65001 >nul
title Настройка проекта
color 0A

echo ========================================
echo 🔧 НАСТРОЙКА ПРОЕКТА
echo ========================================
echo.

echo 1. Создание структуры папок...
echo --------------------------------

mkdir data 2>nul
mkdir data\predictions 2>nul
mkdir data\history 2>nul
mkdir data\stats 2>nul
mkdir data\logs 2>nul
mkdir data\backups 2>nul
mkdir data\models 2>nul
mkdir data\cache 2>nul
mkdir archives 2>nul

echo ✅ Папки созданы
echo.

echo 2. Организация файлов...
echo --------------------------------

REM Перемещаем файлы предсказаний
if exist predictions_history_*.csv (
    echo Перемещение predictions_history_*.csv...
    move predictions_history_*.csv data\history\ 2>nul
)

if exist signals_history_*.csv (
    echo Перемещение signals_history_*.csv...
    move signals_history_*.csv data\history\ 2>nul
)

if exist predictions_stats_*.txt (
    echo Перемещение predictions_stats_*.txt...
    move predictions_stats_*.txt data\stats\ 2>nul
)

if exist predictions_stats_*.json (
    echo Перемещение predictions_stats_*.json...
    move predictions_stats_*.json data\stats\ 2>nul
)

REM Основные файлы данных
if exist predictions.json (
    echo Перемещение predictions.json...
    move predictions.json data\predictions\ 2>nul
)

if exist prediction_stats.json (
    echo Перемещение prediction_stats.json...
    move prediction_stats.json data\stats\ 2>nul
)

if exist xgboost_model.pkl (
    echo Перемещение xgboost_model.pkl...
    move xgboost_model.pkl data\models\ 2>nul
)

if exist xgboost_model_features.json (
    echo Перемещение xgboost_model_features.json...
    move xgboost_model_features.json data\models\ 2>nul
)

REM Базы данных
if exist matches_history.db (
    echo Перемещение matches_history.db...
    move matches_history.db data\history\ 2>nul
)

if exist football_cache.db (
    echo Перемещение football_cache.db...
    move football_cache.db data\cache\ 2>nul
)

REM Логи
if exist *.log (
    echo Перемещение логов...
    move *.log data\logs\ 2>nul
)

REM Бэкапы
if exist *.backup (
    echo Перемещение бэкапов...
    move *.backup data\backups\ 2>nul
)

if exist *.back (
    echo Перемещение бэкапов...
    move *.back data\backups\ 2>nul
)

echo ✅ Файлы организованы
echo.

echo 3. Создание .gitkeep файлов...
echo --------------------------------
echo. > data\.gitkeep 2>nul
echo. > data\predictions\.gitkeep 2>nul
echo. > data\history\.gitkeep 2>nul
echo. > data\stats\.gitkeep 2>nul
echo. > data\logs\.gitkeep 2>nul
echo. > data\backups\.gitkeep 2>nul
echo. > data\models\.gitkeep 2>nul
echo. > data\cache\.gitkeep 2>nul
echo. > archives\.gitkeep 2>nul

echo ✅ .gitkeep файлы созданы
echo.

echo 4. Проверка результата...
echo --------------------------------
dir data /s /b

echo.
echo ========================================
echo ✅ НАСТРОЙКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Теперь можно запустить бота: python run_fixed.py
echo.
pause