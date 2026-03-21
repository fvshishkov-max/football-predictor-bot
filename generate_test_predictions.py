# generate_test_predictions.py
"""
Генерация тестовых предсказаний для анализа
"""

import json
import random
from datetime import datetime, timedelta

def generate_test_predictions():
    """Генерирует тестовые предсказания для анализа"""
    
    teams = [
        ("Arsenal", "Chelsea"), ("Liverpool", "Man City"), ("Barcelona", "Real Madrid"),
        ("Bayern", "Dortmund"), ("PSG", "Marseille"), ("Juventus", "Milan"),
        ("Ajax", "PSV"), ("Benfica", "Porto"), ("Celtic", "Rangers"),
        ("Galatasaray", "Fenerbahce"), ("Zenit", "Spartak"), ("Shakhtar", "Dynamo Kyiv")
    ]
    
    conf_levels = ["VERY_HIGH", "HIGH", "MEDIUM", "LOW"]
    minutes = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
    
    predictions = []
    
    for i in range(100):
        home, away = random.choice(teams)
        prob = random.uniform(0.45, 0.75)
        conf = random.choice(conf_levels)
        minute = random.choice(minutes)
        was_correct = random.random() < (prob - 0.4)  # Чем выше вероятность, тем больше шанс
        
        pred = {
            'match_id': 100000 + i,
            'home_team': home,
            'away_team': away,
            'goal_probability': round(prob, 3),
            'confidence_level': conf,
            'minute': minute,
            'was_correct': was_correct,
            'timestamp': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            'signal': True if prob > 0.48 else None
        }
        predictions.append(pred)
    
    data = {
        'predictions': predictions,
        'accuracy_stats': {
            'total_predictions': len(predictions),
            'correct_predictions': sum(1 for p in predictions if p['was_correct']),
            'incorrect_predictions': len(predictions) - sum(1 for p in predictions if p['was_correct']),
            'accuracy_rate': sum(1 for p in predictions if p['was_correct']) / len(predictions)
        }
    }
    
    # Сохраняем
    os.makedirs('data/predictions', exist_ok=True)
    with open('data/predictions/predictions_test.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Создано 100 тестовых предсказаний")
    print(f"   Сбылось: {data['accuracy_stats']['correct_predictions']}")
    print(f"   Точность: {data['accuracy_stats']['accuracy_rate']*100:.1f}%")

if __name__ == "__main__":
    import os
    generate_test_predictions()