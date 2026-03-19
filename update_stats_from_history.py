# update_stats_from_history.py
"""
Обновляет статистику на основе реальных результатов матчей
"""

import json
import sqlite3
from datetime import datetime

def update_stats_from_history():
    """Обновляет was_correct на основе реальных результатов"""
    
    # Загружаем предсказания
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
        print("❌ Файл с предсказаниями не найден")
        return
    
    # Подключаемся к базе данных истории
    db_path = 'data/history/matches_history.db'
    if not os.path.exists(db_path):
        print("❌ База данных истории не найдена")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print(f"📊 Предсказаний в файле: {len(predictions)}")
    
    updated_count = 0
    correct_count = 0
    
    for pred in predictions:
        match_id = pred.get('match_id')
        
        # Ищем матч в базе
        cursor.execute("""
            SELECT home_score, away_score, is_finished 
            FROM matches WHERE match_id = ?
        """, (match_id,))
        
        result = cursor.fetchone()
        
        if result and result[2]:  # Матч завершен
            home_score, away_score, _ = result
            total_goals = home_score + away_score
            
            had_goal = total_goals > 0
            prob = pred.get('goal_probability', 0)
            predicted_goal = prob > 0.5
            
            was_correct = (had_goal == predicted_goal)
            pred['was_correct'] = was_correct
            updated_count += 1
            
            if was_correct:
                correct_count += 1
    
    conn.close()
    
    if updated_count > 0:
        # Обновляем статистику
        stats['total_predictions'] = updated_count
        stats['correct_predictions'] = correct_count
        stats['incorrect_predictions'] = updated_count - correct_count
        stats['accuracy_rate'] = correct_count / updated_count if updated_count > 0 else 0
        
        data['predictions'] = predictions
        data['accuracy_stats'] = stats
        
        # Сохраняем
        with open(found_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Обновлено {updated_count} предсказаний")
        print(f"📊 Из них сбылось: {correct_count} ({correct_count/updated_count*100:.1f}%)")
    else:
        print("❌ Нет завершенных матчей для обновления")

if __name__ == "__main__":
    import os
    update_stats_from_history()