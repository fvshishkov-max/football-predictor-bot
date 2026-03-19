@echo off
echo ========================================
echo      СБОР ФАЙЛОВ ДЛЯ АНАЛИЗА
echo ========================================
echo.

set FOLDER=analysis_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set FOLDER=%FOLDER: =0%

mkdir %FOLDER% 2>nul

echo Копирование файлов в папку %FOLDER%...
echo.

if exist signal_accuracy.json (
    copy signal_accuracy.json %FOLDER% >nul
    echo [OK] signal_accuracy.json
) else (
    echo [..] signal_accuracy.json не найден
)

if exist bot_stats.json (
    copy bot_stats.json %FOLDER% >nul
    echo [OK] bot_stats.json
) else (
    echo [..] bot_stats.json не найден
)

if exist football_bot.log (
    copy football_bot.log %FOLDER% >nul
    echo [OK] football_bot.log
) else (
    echo [..] football_bot.log не найден
)

echo.
echo Поиск файлов истории сигналов...
for %%f in (signals_history_*.json) do (
    copy %%f %FOLDER% >nul
    echo [OK] %%f
)

echo.
echo Создание архива...
powershell -Command "Compress-Archive -Path '%FOLDER%\*' -DestinationPath '%FOLDER%.zip' -Force"

if exist %FOLDER%.zip (
    echo.
    echo ========================================
    echo [OK] Файлы собраны в %FOLDER%.zip
    echo ========================================
    echo.
    echo Отправьте этот файл на анализ.
) else (
    echo.
    echo [ОШИБКА] Не удалось создать архив
)

pause