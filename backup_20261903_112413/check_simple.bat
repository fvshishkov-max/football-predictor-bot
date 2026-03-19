@echo off
echo ========================================
echo CHECKING PROJECT FILES
echo ========================================
echo.

set missing=0

call :check run_fixed.py
call :check app.py
call :check predictor.py
call :check telegram_bot.py
call :check stats_reporter.py
call :check translations.py
call :check api_client.py
call :check models.py
call :check config.py
call :check team_form.py
call :check betting_optimizer.py

echo.
if %missing% equ 0 (
    echo All core files present
) else (
    echo Missing %missing% files
)

echo.
echo Python files count:
dir *.py /b | find /c /v ""
echo.

echo.
echo ========================================
pause
exit /b

:check
if exist %1 (
    echo [OK] %1
) else (
    echo [MISSING] %1
    set /a missing+=1
)
exit /b