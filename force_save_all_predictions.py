# force_save_all_predictions.py
"""
Принудительное сохранение всех предсказаний из памяти бота
Запуск: python force_save_all_predictions.py
"""

import json
import os
import sys
from datetime import datetime

def force_save():
    """Принудительно сохраняет все предсказания"""
    
    # Пытаемся импортировать предсказания из памяти
    try:
        from predictor import Predictor
        predictor = Predictor()
        
        print("="*80)
        print("💾 ПРИНУДИТЕЛЬНОЕ СОХРАНЕНИЕ ПРЕДСКАЗАНИЙ")
        print("="*80)
        
        print(f"\n📊 Предсказаний в памяти: {len(predictor.predictions_history)}")
        
        if len(predictor.predictions_history) > 0:
            # Сохраняем
            predictor.save_predictions()
            print(f"✅ Сохранено {len(predictor.predictions_history)} предсказаний")
            
            # Проверяем файл
            with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved = data.get('predictions', [])
                print(f"📁 В файле: {len(saved)} предсказаний")
        else:
            print("⚠️ В памяти нет предсказаний")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    force_save()