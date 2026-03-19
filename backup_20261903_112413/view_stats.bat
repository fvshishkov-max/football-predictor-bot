@echo off
echo ========================================
echo PROJECT STATISTICS
echo ========================================
echo.

echo 📁 DATA FOLDER STRUCTURE:
echo -------------------------
tree data /f

echo.
echo 📊 FILE COUNTS:
echo -------------------------
echo Python files: 
dir *.py /b /s | find /c /v ""

echo Data files:
dir data /b /s | find /c /v ""

echo.
echo 📈 LATEST PREDICTIONS:
echo -------------------------
if exist data\predictions\predictions.json (
    echo Last 5 predictions:
    powershell -Command "Get-Content data\predictions\predictions.json | ConvertFrom-Json | Select-Object -ExpandProperty predictions | Select-Object -Last 5 | ForEach-Object { $_.timestamp + ' - ' + $_.home_team + ' vs ' + $_.away_team + ': ' + $_.goal_probability }"
) else (
    echo No predictions file found
)

echo.
echo 📊 STATISTICS:
echo -------------------------
if exist data\stats\prediction_stats.json (
    powershell -Command "Get-Content data\stats\prediction_stats.json | ConvertFrom-Json | Select-Object total_predictions, correct_predictions, accuracy_rate"
) else (
    echo No stats file found
)

echo.
echo ========================================
pause