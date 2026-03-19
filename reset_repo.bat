@echo off
chcp 1251 >nul
title Сброс репозитория
color 0A

echo ========================================
====
echo ⚠️  ПОЛНЫЙ СБРОС РЕПОЗИТОРИЯ
echo ========================================
====
echo.
echo ВНИМАНИЕ! Это удалит все изменения и
echo синхронизирует репозиторий с локальной папкой!
echo.

set /p CONFIRM="Вы уверены? (YES/NO): "

if /i "%CONFIRM%"=="YES" (
    echo.
    echo 1. Сохранение важных файлов...
    mkdir temp_backup 2>nul
    copy *.py temp_backup\ 2>nul
    copy *.bat temp_backup\ 2>nul
    copy .env temp_backup\ 2>nul
    echo   ✅ Резервная копия в temp_backup
    echo.
    
    echo 2. Полная очистка Git...
    git rm -r --cached . >nul 2>nul
    echo   ✅ Индекс очищен
    echo.
    
    echo 3. Добавление только нужных файлов...
    git add *.py
    git add *.bat
    if exist .env git add .env
    git add .gitignore
    git add requirements.txt
    if exist README.md git add README.md
    echo   ✅ Файлы добавлены
    echo.
    
    echo 4. Создание коммита...
    git commit -m "Reset repository - clean source files only"
    echo.
    
    echo 5. Отправка на GitHub...
    git push origin main --force
    echo.
    
    echo ========================================
====
    echo ✅ РЕПОЗИТОРИЙ СБРОШЕН
    echo ========================================
====
) else (
    echo.
    echo ⏹ Отменено
)

pause