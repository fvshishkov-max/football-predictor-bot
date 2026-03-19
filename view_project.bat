@echo off
chcp 65001 >nul
title Структура проекта
color 0A

echo ========================================
echo 📋 СТРУКТУРА ПРОЕКТА
echo ========================================
echo.

echo Основные файлы:
echo ---------------
dir *.py /b
echo.

echo Папка data:
echo ---------------
if exist data (
    tree data /f
) else (
    echo Папка data не найдена
)

echo.
echo Статистика:
echo ---------------
set pycount=0
for %%f in (*.py) do set /a pycount+=1
echo Python файлов: %pycount%

if exist data (
    set datacount=0
    for /r data %%f in (*) do set /a datacount+=1
    echo Файлов в data: %datacount%
)

echo.
echo ========================================
pause