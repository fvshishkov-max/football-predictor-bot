# update_config.py
"""
Скрипт для обновления путей в файлах проекта
"""

import os
import re

def update_file(file_path, old_path, new_path):
    """Обновляет пути в файле"""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем старые пути на новые
    new_content = content.replace(old_path, new_path)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Обновлен: {file_path}")
        return True
    else:
        print(f"⏺ Без изменений: {file_path}")
        return False

def main():
    print("="*50)
    print("🔄 ОБНОВЛЕНИЕ ПУТЕЙ В ФАЙЛАХ")
    print("="*50)
    
    # Список файлов для обновления
    files = [
        'predictor.py',
        'stats_reporter.py',
        'team_form.py',
        'api_client.py',
        'app.py'
    ]
    
    # Соответствия старых и новых путей
    replacements = [
        ('predictions.json', 'data/predictions/predictions.json'),
        ('prediction_stats.json', 'data/stats/prediction_stats.json'),
        ('matches_history.db', 'data/history/matches_history.db'),
        ('football_cache.db', 'data/cache/football_cache.db'),
        ('xgboost_model.pkl', 'data/models/xgboost_model.pkl'),
        ('app.log', 'data/logs/app.log'),
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"\n📄 Обработка: {file}")
            for old, new in replacements:
                update_file(file, old, new)
    
    print("\n" + "="*50)
    print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    print("="*50)

if __name__ == "__main__":
    main()