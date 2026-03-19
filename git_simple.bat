@echo off
echo ========================================
echo GIT UPDATE
echo ========================================
echo.

echo 1. Git status:
git status

echo.
echo 2. Adding files...
git add .

echo.
echo 3. Git status after add:
git status

echo.
echo 4. Enter commit message:
set /p msg="> "

if "%msg%"=="" (
    set msg=Update %date%
)

echo.
echo 5. Creating commit...
git commit -m "%msg%"

echo.
echo 6. Pushing to GitHub...
git push origin main

echo.
echo ========================================
echo DONE
echo ========================================
pause