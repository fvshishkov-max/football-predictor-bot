# fix_predictions_file.py
"""
Исправление поврежденного файла predictions.json
"""

import json
import os

def fix_predictions_file():
    """Исправляет или удаляет поврежденный файл"""
    
    files_to_check = [
        'data/predictions.json',
        'predictions.json',
        'data/predictions/predictions.json'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {file} - OK")
            except Exception as e:
                print(f"❌ {file} - поврежден: {e}")
                # Создаем резервную копию
                backup = f"{file}.broken"
                os.rename(file, backup)
                print(f"   Создана резервная копия: {backup}")
                
                # Создаем новый файл
                new_data = {
                    'predictions': [],
                    'accuracy_stats': {
                        'total_predictions': 0,
                        'correct_predictions': 0,
                        'incorrect_predictions': 0,
                        'accuracy_rate': 0.0,
                        'by_confidence': {}
                    },
                    'thresholds': {'low': 0.15, 'medium': 0.25, 'high': 0.40, 'very_high': 0.55},
                    'half_goals': {},
                    'match_signal_count': {},
                    'min_signal_probability': 0.48
                }
                
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                print(f"   Создан новый файл: {file}")

if __name__ == "__main__":
    fix_predictions_file()
    print("\n✅ Готово! Перезапустите бота: python run_fixed.py")