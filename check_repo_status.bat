@echo off
chcp 1251 >nul
title Статус репозитория
color 0A

echo ========================================
====
echo 📊 СТАТУС РЕПОЗИТОРИЯ
echo ========================================
====
echo.

echo 1. Локальные изменения:
echo -------------------------
git status --short
echo.

echo 2. Последние коммиты:
echo ----------------------
git log --oneline -5
echo.

echo 3. Отличия от удаленного репозитория:
echo --------------------------------------
git fetch
git log origin/main..HEAD --oneline
echo.

echo 4. Неотслеживаемые файлы:
echo --------------------------
git ls-files --others --exclude-standard
echo.

echo ========================================
====
pause