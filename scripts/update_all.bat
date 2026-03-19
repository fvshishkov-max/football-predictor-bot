@echo off
chcp 1251 >nul
title Полное обновление
color 0A

echo ========================================
echo 🔄 ПОЛНОЕ ОБНОВЛЕНИЕ
echo ========================================
echo.

git add .
git commit -m "Update: %date% %time%"
git push origin main

echo.
echo ========================================
pause
