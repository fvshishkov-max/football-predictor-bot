@echo off
chcp 65001 >nul
title Быстрая синхронизация
color 0A

echo ========================================
echo ⚡ БЫСТРАЯ СИНХРОНИЗАЦИЯ
echo ========================================
echo.

git add .
git commit -m "Quick sync %date% %time%"
git push

echo.
echo ✅ Готово!
pause