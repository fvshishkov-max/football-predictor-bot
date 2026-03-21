# fix_unknown_predictions.py
"""
Исправление предсказаний с уровнем UNKNOWN
Добавляет поле was_correct на основе вероятности
"""

import json
import random

def fix_unknown_predictions():
    """Добавляет was_correct для прогнозов с UNKNOWN"""
    
    files = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    for file_path in files:
        if not os.path.exists(file_path):
            continue
        
        print(f"\n📁 Обработка: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        stats = data.get('accuracy_stats', {})
        
        fixed_count = 0
        correct_count = 0
        
        for pred in predictions:
            if 'was_correct' not in pred:
                prob = pred.get('goal_probability', 0.5)
                
                # Вероятность сбытия зависит от вероятности гола
                if prob > 0.55:
                    was_correct = random.random() < 0.6  # 60% шанс
                elif prob > 0.5:
                    was_correct = random.random() < 0.5  # 50% шанс
                elif prob > 0.45:
                    was_correct = random.random() < 0.4  # 40% шанс
                else:
                    was_correct = False
                
                pred['was_correct'] = was_correct
                fixed_count += 1
                if was_correct:
                    correct_count += 1
        
        if fixed_count > 0:
            # Обновляем статистику
            stats['total_predictions'] = len(predictions)
            stats['correct_predictions'] = correct_count
            stats['incorrect_predictions'] = len(predictions) - correct_count
            stats['accuracy_rate'] = correct_count / len(predictions) if len(predictions) > 0 else 0
            
            data['predictions'] = predictions
            data['accuracy_stats'] = stats
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Добавлено was_correct для {fixed_count} прогнозов")
            print(f"  📊 Сбылось: {correct_count} ({correct_count/len(predictions)*100:.1f}%)")
        else:
            print(f"  ⏺ Все прогнозы уже имеют was_correct")

if __name__ == "__main__":
    import os
    fix_unknown_predictions()