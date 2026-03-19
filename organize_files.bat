@echo off
echo ========================================
echo ORGANIZING PROJECT FILES
echo ========================================
echo.

REM Создаем папки
call create_folders.bat

echo Moving files...

REM Перемещаем файлы предсказаний
if exist predictions_history_*.csv move predictions_history_*.csv data\history\ 2>nul
if exist signals_history_*.csv move signals_history_*.csv data\history\ 2>nul
if exist predictions_stats_*.txt move predictions_stats_*.txt data\stats\ 2>nul
if exist predictions_stats_*.json move predictions_stats_*.json data\stats\ 2>nul

REM Перемещаем основные файлы данных
if exist predictions.json move predictions.json data\predictions\ 2>nul
if exist prediction_stats.json move prediction_stats.json data\stats\ 2>nul
if exist xgboost_model.pkl move xgboost_model.pkl data\models\ 2>nul
if exist xgboost_model_features.json move xgboost_model_features.json data\models\ 2>nul

REM Перемещаем базы данных
if exist matches_history.db move matches_history.db data\history\ 2>nul
if exist football_cache.db move football_cache.db data\cache\ 2>nul

REM Перемещаем логи
if exist *.log move *.log data\logs\ 2>nul

REM Перемещаем бэкапы
if exist *.backup move *.backup data\backups\ 2>nul
if exist *.back move *.back data\backups\ 2>nul

echo [OK] Files organized
echo.

echo Checking result:
dir data /s /b

echo.
echo ========================================
pause