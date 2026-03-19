@echo off
echo Создание .gitkeep файлов...

echo. > data\.gitkeep 2>nul
echo. > data\predictions\.gitkeep 2>nul
echo. > data\history\.gitkeep 2>nul
echo. > data\stats\.gitkeep 2>nul
echo. > data\logs\.gitkeep 2>nul
echo. > data\backups\.gitkeep 2>nul
echo. > data\models\.gitkeep 2>nul
echo. > data\cache\.gitkeep 2>nul
echo. > archives\.gitkeep 2>nul

echo ✅ .gitkeep файлы созданы
pause