@echo off
chcp 1251 >nul
title Экстренное восстановление
color 0A

echo ========================================
====
echo 🚑 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ
echo ========================================
====
echo.

REM ========================================
REM 1. Создаем все папки
REM ========================================
echo 1. ВОССТАНОВЛЕНИЕ ПАПОК:
echo -------------------------

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

REM ========================================
REM 2. Создаем .gitkeep файлы
REM ========================================
echo 2. СОЗДАНИЕ .GITKEEP:
echo ---------------------

echo # Папка для данных > data\README.txt
echo Сюда сохраняются файлы данных бота >> data\README.txt

echo. > data\.gitkeep
echo. > data\predictions\.gitkeep
echo. > data\history\.gitkeep
echo. > data\stats\.gitkeep
echo. > data\logs\.gitkeep
echo. > data\backups\.gitkeep
echo. > data\models\.gitkeep
echo. > data\cache\.gitkeep
echo. > archives\.gitkeep

echo   ✅ .gitkeep созданы
echo.

REM ========================================
REM 3. Добавляем в Git
REM ========================================
echo 3. ДОБАВЛЕНИЕ В GIT:
echo ---------------------

git add data\README.txt
git add data\.gitkeep
git add data\predictions\.gitkeep
git add data\history\.gitkeep
git add data\stats\.gitkeep
git add data\logs\.gitkeep
git add data\backups\.gitkeep
git add data\models\.gitkeep
git add data\cache\.gitkeep
git add archives\.gitkeep

echo   ✅ Файлы добавлены
echo.

REM ========================================
REM 4. Правильный .gitignore
REM ========================================
echo 4. НАСТРОЙКА .GITIGNORE:
echo -------------------------

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
echo.
echo # Data folders - сохраняем структуру
echo data/*
echo !data/.gitkeep
echo !data/README.txt
echo !data/predictions/.gitkeep
echo !data/history/.gitkeep
echo !data/stats/.gitkeep
echo !data/logs/.gitkeep
echo !data/backups/.gitkeep
echo !data/models/.gitkeep
echo !data/cache/.gitkeep
echo archives/*
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
echo # Temporary
echo *.tmp
echo *.temp
echo *~
echo.
echo # IDE
echo .vscode/
echo .idea/
) > .gitignore

git add .gitignore
echo   ✅ .gitignore обновлен
echo.

REM ========================================
REM 5. Коммит и пуш
REM ========================================
echo 5. ОТПРАВКА НА GITHUB:
echo -----------------------

git commit -m "Emergency fix: restore folder structure"
git push origin main

echo.
echo ========================================
====
echo ✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО
echo ========================================
====
pause