# update_match_results.py
"""
Обновление результатов предсказанных матчей
Запуск: python update_match_results.py
"""

import json
import requests
from datetime import datetime

def get_match_result(match_name):
    """
    Здесь нужно получать реальные результаты матчей
    Пока используем ручной ввод
    """
    print(f"\n📋 Матч: {match_name}")
    print("Введите результат (формат: голы_хозяев:голы_гостей)")
    print("Пример: 2:1, 0:0, 3:0")
    result = input("Результат: ").strip()
    
    try:
        home_goals, away_goals = map(int, result.split(':'))
        return home_goals, away_goals
    except:
        print("❌ Неверный формат! Используйте формат X:Y")
        return None, None

def update_predictions():
    """Обновляет was_correct для предсказаний"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print("="*70)
    print("⚽ ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ МАТЧЕЙ")
    print("="*70)
    print(f"\n📊 Всего предсказаний: {len(predictions)}")
    
    # Обновляем только те, у которых нет результата
    to_update = [p for p in predictions if p.get('was_correct') is None]
    
    if not to_update:
        print("\n✅ Все предсказания уже имеют результаты!")
        return
    
    print(f"\n📋 Нужно обновить: {len(to_update)} матчей")
    print("-"*70)
    
    updated_count = 0
    correct_count = 0
    
    for pred in to_update:
        home = pred.get('home_team', 'Unknown')
        away = pred.get('away_team', 'Unknown')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        
        print(f"\n🏟 {home} vs {away}")
        print(f"   ⏱ {minute}' | 📊 {prob:.1f}%")
        
        # Получаем результат
        home_goals, away_goals = get_match_result(f"{home} vs {away}")
        
        if home_goals is not None:
            total_goals = home_goals + away_goals
            had_goal = total_goals > 0
            predicted_goal = prob > 46  # порог отправки
            
            was_correct = (had_goal == predicted_goal)
            
            pred['was_correct'] = was_correct
            pred['home_score'] = home_goals
            pred['away_score'] = away_goals
            
            updated_count += 1
            if was_correct:
                correct_count += 1
                print(f"   ✅ ПРОГНОЗ СБЫЛСЯ!")
            else:
                print(f"   ❌ ПРОГНОЗ НЕ СБЫЛСЯ")
    
    # Обновляем статистику
    total = len(predictions)
    stats['total_predictions'] = total
    stats['correct_predictions'] = correct_count
    stats['incorrect_predictions'] = total - correct_count
    stats['accuracy_rate'] = correct_count / total if total > 0 else 0
    
    # Обновляем статистику по уверенности
    for pred in predictions:
        conf = pred.get('confidence_level', 'MEDIUM')
        if conf not in stats['by_confidence']:
            stats['by_confidence'][conf] = {'total': 0, 'correct': 0}
        
        stats['by_confidence'][conf]['total'] += 1
        if pred.get('was_correct', False):
            stats['by_confidence'][conf]['correct'] += 1
    
    # Сохраняем
    with open('data/predictions/predictions.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("📊 ОБНОВЛЕННАЯ СТАТИСТИКА:")
    print("-"*70)
    print(f"  Всего предсказаний: {total}")
    print(f"  ✅ Сбылось: {correct_count}")
    print(f"  ❌ Не сбылось: {total - correct_count}")
    print(f"  🎯 Точность: {correct_count/total*100:.1f}%")
    print("="*70)

def auto_update_from_api():
    """
    Автоматическое обновление из API (заглушка)
    """
    print("\n🔧 Для автоматического обновления нужно подключить API")
    print("   Например: Football-Data.org, SStats API")
    print("   Пока используем ручной ввод\n")

if __name__ == "__main__":
    print("\nВыберите режим:")
    print("1. Ручной ввод результатов")
    print("2. Автоматическое обновление (в разработке)")
    print("3. Пропустить")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        update_predictions()
    elif choice == '2':
        auto_update_from_api()
    else:
        print("Обновление отменено")