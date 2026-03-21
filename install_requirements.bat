@echo off
chcp 65001 >nul
title Install Requirements
color 0A

echo ========================================
echo INSTALLING REQUIREMENTS
echo ========================================
echo.

echo Installing xgboost...
pip install xgboost

echo.
echo Installing other packages...
pip install numpy pandas scikit-learn joblib

echo.
echo ========================================
echo DONE
echo ========================================
pause