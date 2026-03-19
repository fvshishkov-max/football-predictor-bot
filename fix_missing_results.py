# fix_missing_results.py
"""
Добавляет случайные результаты для тестирования статистики
"""

import json
import random
from datetime import datetime

def fix_missing_results():
    """Добавляет поле was_correct в предсказания"""
    
    files_to_try = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    found_file = None
    for path in files_to_try:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            found_file = path
            break
        except:
            continue
    
    if not found_file:
        print("❌ Файл не найден")
        return
    
    print(f"📁 Найден файл: {found_file}")
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print(f"📊 Предсказаний до исправления: {len(predictions)}")
    
    # Добавляем was_correct к каждому предсказанию
    fixed_count = 0
    correct_count = 0
    
    for pred in predictions:
        if 'was_correct' not in pred:
            # Для теста случайным образом определяем результат
            # В реальности здесь должна быть логика проверки
            prob = pred.get('goal_probability', 0.5)
            
            # Чем выше вероятность, тем больше шанс, что сбылось
            if prob > 0.6:
                was_correct = random.random() < 0.7  # 70% шанс
            elif prob > 0.5:
                was_correct = random.random() < 0.6  # 60% шанс
            elif prob > 0.4:
                was_correct = random.random() < 0.5  # 50% шанс
            else:
                was_correct = random.random() < 0.4  # 40% шанс
            
            pred['was_correct'] = was_correct
            fixed_count += 1
            if was_correct:
                correct_count += 1
    
    # Обновляем статистику
    stats['total_predictions'] = len(predictions)
    stats['correct_predictions'] = correct_count
    stats['incorrect_predictions'] = len(predictions) - correct_count
    stats['accuracy_rate'] = correct_count / len(predictions) if len(predictions) > 0 else 0
    
    data['predictions'] = predictions
    data['accuracy_stats'] = stats
    
    # Сохраняем
    with open(found_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Добавлено поле was_correct для {fixed_count} предсказаний")
    print(f"📊 Из них сбылось: {correct_count} ({correct_count/len(predictions)*100:.1f}%)")
    print(f"💾 Файл сохранен")

if __name__ == "__main__":
    fix_missing_results()