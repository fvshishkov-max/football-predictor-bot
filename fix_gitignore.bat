@echo off
chcp 1251 >nul
title Настройка .gitignore
color 0A

echo ========================================
====
echo 🔧 НАСТРОЙКА .GITIGNORE
echo ========================================
====
echo.

REM ========================================
REM 1. Создаем правильный .gitignore
REM ========================================
echo 1. СОЗДАНИЕ .GITIGNORE:
echo ------------------------

(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo env/
echo venv/
echo ENV/
echo env.bak/
echo venv.bak/
echo.
echo # Data folders - НО СОХРАНЯЕМ .gitkeep
echo data/
echo !data/.gitkeep
echo data/predictions/
echo !data/predictions/.gitkeep
echo data/history/
echo !data/history/.gitkeep
echo data/stats/
echo !data/stats/.gitkeep
echo data/logs/
echo !data/logs/.gitkeep
echo data/backups/
echo !data/backups/.gitkeep
echo data/models/
echo !data/models/.gitkeep
echo data/cache/
echo !data/cache/.gitkeep
echo archives/
echo !archives/.gitkeep
echo.
echo # Logs
echo *.log
echo *.log.*
echo.
echo # Backups
echo *.backup
echo *.back
echo *.bak
echo.
echo # Temporary files
echo *.tmp
echo *.temp
echo *.swp
echo *.swo
echo *~
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.sublime-*
echo.
echo # Test files
echo test_*.py
echo !test_telegram.py
echo debug_*.py
echo diagnose_*.py
echo.
echo # Xray
echo xray/
echo xray.exe
echo access.log
echo error.log
echo.
echo # Local configuration
echo .env
echo config.local.py
) > .gitignore

echo   ✅ .gitignore создан
echo.

REM ========================================
REM 2. Проверяем результат
REM ========================================
echo 2. СОДЕРЖИМОЕ .GITIGNORE:
echo --------------------------
type .gitignore
echo.

REM ========================================
REM 3. Добавляем в Git
REM ========================================
echo 3. ДОБАВЛЕНИЕ В GIT:
echo ---------------------
git add .gitignore
echo   ✅ .gitignore добавлен
echo.

REM ========================================
REM 4. Создаем коммит
REM ========================================
set /p COMMIT="Введите комментарий: "
if "%COMMIT%"=="" set COMMIT="Update .gitignore to preserve folder structure"

git commit -m "%COMMIT%"
echo.

REM ========================================
REM 5. Отправка на GitHub
REM ========================================
echo 4. ОТПРАВКА НА GITHUB:
echo -----------------------
git push origin main
echo.

echo ========================================
====
echo ✅ .GITIGNORE НАСТРОЕН
echo ========================================
====
pause