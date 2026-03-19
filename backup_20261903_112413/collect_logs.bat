@echo off
echo Сбор файлов для анализа...
echo.

set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set FOLDER=analysis_%TIMESTAMP%

mkdir %FOLDER%

echo Копирование файлов в папку %FOLDER%...
echo.

copy signal_accuracy.json %FOLDER%\ 2>nul && echo ✅ signal_accuracy.json || echo ❌ signal_accuracy.json не найден
copy bot_stats.json %FOLDER%\ 2>nul && echo ✅ bot_stats.json || echo ❌ bot_stats.json не найден
copy football_bot.log %FOLDER%\ 2>nul && echo ✅ football_bot.log || echo ❌ football_bot.log не найден

dir /b signals_history_*.json > temp.txt
for /f "tokens=*" %%a in (temp.txt) do (
    copy "%%a" %FOLDER%\ 2>nul && echo ✅ %%a
)
del temp.txt

echo.
echo Создание архива...
powershell Compress-Archive -Path %FOLDER%\* -DestinationPath %FOLDER%.zip -Force

echo.
echo ✅ Готово! Файлы собраны в %FOLDER%.zip
echo Отправьте этот архив на анализ.
pause