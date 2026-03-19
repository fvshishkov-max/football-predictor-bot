@echo off
chcp 1251 >nul
title Содержимое репозитория
color 0A

echo ========================================
====
echo 📋 ЧТО В РЕПОЗИТОРИИ
echo ========================================
====
echo.

echo 1. ПОСЛЕДНИЙ КОММИТ:
echo ---------------------
git log -1 --pretty=format:"%%h - %%s (%%cr)"
echo.
echo.

echo 2. ФАЙЛЫ В РЕПОЗИТОРИИ:
echo ------------------------
git ls-tree -r main --name-only | findstr /v "data/ archives/ *.log *.csv *.txt"
echo.

echo 3. ПАПКИ В РЕПОЗИТОРИИ:
echo ------------------------
git ls-tree -r main --name-only | findstr /r ".*/" | sort | uniq
echo.

echo 4. РАЗМЕР РЕПОЗИТОРИЯ:
echo -----------------------
git count-objects -vH
echo.

echo ========================================
====
pause