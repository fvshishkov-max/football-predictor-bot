@echo off
echo ========================================
echo LISTING ALL FILES
echo ========================================
echo.

echo Python files:
dir *.py /b
echo.

echo Data folder:
if exist data (
    dir data /b
) else (
    echo No data folder
)
echo.

echo Xray folder:
if exist xray (
    dir xray /b
) else (
    echo No xray folder
)

echo.
echo ========================================
pause