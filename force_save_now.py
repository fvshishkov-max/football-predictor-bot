# force_save_now.py
"""
Принудительное сохранение всех предсказаний из памяти
Запуск: python force_save_now.py
"""

import json
import os
from datetime import datetime

def force_save():
    print("="*80)
    print("💾 ПРИНУДИТЕЛЬНОЕ СОХРАНЕНИЕ")
    print("="*80)
    
    # Импортируем и создаем экземпляр
    from predictor import Predictor
    predictor = Predictor()
    
    print(f"\n📊 Предсказаний в памяти: {len(predictor.predictions_history)}")
    
    # Показываем последние предсказания
    if predictor.predictions_history:
        print("\n📋 ПОСЛЕДНИЕ 5 ПРЕДСКАЗАНИЙ:")
        for pred in predictor.predictions_history[-5:]:
            home = pred.get('home_team', '?')
            away = pred.get('away_team', '?')
            prob = pred.get('goal_probability', 0) * 100
            minute = pred.get('minute', 0)
            ts = pred.get('timestamp', '')[:16]
            print(f"  {ts} | {minute}' | {home} vs {away} | {prob:.1f}%")
    
    # Сохраняем
    predictor.save_predictions()
    print(f"\n✅ Сохранено в data/predictions/predictions.json")
    
    # Проверяем файл
    if os.path.exists('data/predictions/predictions.json'):
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            saved = data.get('predictions', [])
            print(f"📁 В файле: {len(saved)} предсказаний")
            
            if saved:
                last = saved[-1]
                print(f"🕐 Последнее: {last.get('timestamp', '')[:16]}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    force_save()