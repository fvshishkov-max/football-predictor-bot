@echo off
chcp 65001 >nul
title Список файлов
color 0A

echo ========================================
echo 📋 СПИСОК ВСЕХ ФАЙЛОВ
echo ========================================
echo.

dir /s /b > file_list.txt

echo Файлы сохранены в file_list.txt
echo.
echo Основные файлы проекта:
echo -----------------------
dir *.py /b
echo.
echo Папка data:
dir data /b 2>nul
echo.
echo Папка xray:
dir xray /b 2>nul

echo.
echo ========================================
pause