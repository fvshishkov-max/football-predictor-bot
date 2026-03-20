@echo off
chcp 1251 >nul
title Анализ статистики
color 0A

echo ========================================
echo 📊 АНАЛИЗ СТАТИСТИКИ ПРОГНОЗОВ
echo ========================================
echo.

echo 1. Анализ времени голов...
python analyze_goal_times.py
echo.

echo 2. Обновление анализатора на основе статистики...
python update_match_analyzer.py
echo.

echo 3. Проверка текущих предсказаний...
python -c "import json; f=open('data/predictions/predictions.json'); d=json.load(f); print(f'Всего предсказаний: {len(d.get(\"predictions\", []))}')" 2>nul
echo.

echo ========================================
pause