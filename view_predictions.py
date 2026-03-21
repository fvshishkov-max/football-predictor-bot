# view_predictions.py
"""
Просмотр предсказаний из JSON файла
Запуск: python view_predictions.py
"""

import json
import sys

def view_predictions():
    """Показывает последние предсказания"""
    
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        
        print("="*70)
        print("📊 ПРЕДСКАЗАНИЯ В ПРОЕКТЕ")
        print("="*70)
        print(f"\n📈 Всего предсказаний: {len(predictions)}")
        
        if predictions:
            print("\n📋 ПОСЛЕДНИЕ 5 ПРЕДСКАЗАНИЙ:")
            print("-"*70)
            
            for i, pred in enumerate(predictions[-5:], 1):
                ts = pred.get('timestamp', '')[:19]
                home = pred.get('home_team', 'Unknown')
                away = pred.get('away_team', 'Unknown')
                prob = pred.get('goal_probability', 0) * 100
                conf = pred.get('confidence_level', 'UNKNOWN')
                minute = pred.get('minute', 0)
                was_correct = pred.get('was_correct', None)
                
                status = ""
                if was_correct is True:
                    status = "✅ ГОЛ"
                elif was_correct is False:
                    status = "❌ НЕТ"
                else:
                    status = "❓ ОЖИДАНИЕ"
                
                print(f"\n  {i}. {ts}")
                print(f"     🏟 {home} vs {away}")
                print(f"     ⏱ {minute}' | 📊 {prob:.1f}% | 🎯 {conf}")
                print(f"     📌 Результат: {status}")
        
        # Общая статистика
        stats = data.get('accuracy_stats', {})
        if stats:
            print("\n📊 ОБЩАЯ СТАТИСТИКА:")
            print("-"*70)
            print(f"  Всего предсказаний: {stats.get('total_predictions', 0)}")
            print(f"  Правильных: {stats.get('correct_predictions', 0)}")
            print(f"  Неправильных: {stats.get('incorrect_predictions', 0)}")
            print(f"  Точность: {stats.get('accuracy_rate', 0)*100:.1f}%")
        
        print("\n" + "="*70)
        
    except FileNotFoundError:
        print("❌ Файл data/predictions/predictions.json не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    view_predictions()