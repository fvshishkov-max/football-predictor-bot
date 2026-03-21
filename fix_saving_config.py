# fix_saving_config.py
"""
Исправление настроек сохранения данных в predictor.py
Запуск: python fix_saving_config.py
"""

import re
import os

def fix_predictor_saving():
    """Исправляет predictor.py для сохранения в JSON, а не CSV"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("="*60)
    print("🔧 ИСПРАВЛЕНИЕ СОХРАНЕНИЯ В PREDICTOR.PY")
    print("="*60)
    
    # 1. Проверяем и исправляем путь сохранения
    old_path = "filename: str = 'data/predictions/predictions.json'"
    new_path = "filename: str = 'data/predictions/predictions.json'"
    
    if old_path in content:
        print("✅ Путь сохранения правильный")
    else:
        # Ищем и заменяем
        content = content.replace("filename: str = 'predictions.json'", new_path)
        content = content.replace("filename: str = 'data/predictions.json'", new_path)
        print("✅ Путь сохранения исправлен")
    
    # 2. Проверяем вызов save_predictions в нужных местах
    # Добавляем вызов после каждого прогноза
    if 'self.save_predictions()' in content:
        print("✅ Вызов save_predictions найден")
    else:
        print("⚠️ Вызов save_predictions не найден")
    
    # 3. Добавляем принудительное сохранение после каждого прогноза
    save_call = """
        # Сохраняем после каждого прогноза
        self.save_predictions()
"""
    
    # Ищем метод analyze_live_match
    if 'def analyze_live_match' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'if signal:' in line and 'return prediction.get' in lines[i+1] if i+1 < len(lines) else False:
                lines.insert(i+2, save_call)
                content = '\n'.join(lines)
                print("✅ Добавлен вызов save_predictions после сигнала")
                break
    
    # 4. Сохраняем изменения
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ predictor.py обновлен")

def fix_stats_reporter():
    """Исправляет stats_reporter.py для правильного сохранения"""
    
    with open('stats_reporter.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n" + "="*60)
    print("🔧 ИСПРАВЛЕНИЕ СОХРАНЕНИЯ В STATS_REPORTER.PY")
    print("="*60)
    
    # Проверяем путь сохранения
    old_path = "self.stats_file = 'data/stats/prediction_stats.json'"
    if old_path in content:
        print("✅ Путь сохранения правильный")
    
    # Добавляем принудительное сохранение после обновления
    if 'self.save_stats()' in content:
        print("✅ Вызов save_stats найден")
    
    print("✅ stats_reporter.py проверен")

def create_missing_folders():
    """Создает недостающие папки"""
    
    folders = [
        'data/logs',
        'data/backups',
        'data/models'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Папка создана: {folder}")

def main():
    fix_predictor_saving()
    fix_stats_reporter()
    create_missing_folders()
    
    print("\n" + "="*60)
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("="*60)
    print("\nТеперь перезапустите бота:")
    print("  python run_fixed.py")
    print("\nЧерез 10 минут проверьте data/predictions/predictions.json")
    print("  python debug_data_saving.py")

if __name__ == "__main__":
    main()