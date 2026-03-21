# update_results_from_api.py
"""
Автоматическое обновление результатов матчей из API
Запуск: python update_results_from_api.py
"""

import json
import requests
import time
from datetime import datetime, timedelta
import config

def get_match_result(match_id, home_team, away_team, match_date):
    """Получает результат матча из SStats API"""
    try:
        url = f"https://api.sstats.net/Games/{match_id}"
        params = {'apikey': config.SSTATS_TOKEN}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            game = data.get('data', {}).get('game', {})
            home_score = game.get('homeResult')
            away_score = game.get('awayResult')
            
            if home_score is not None and away_score is not None:
                return home_score, away_score
    except Exception as e:
        print(f"  Ошибка получения результата для матча {match_id}: {e}")
    
    return None, None

def update_predictions():
    """Обновляет результаты в predictions.json"""
    
    # Загружаем предсказания
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print("="*80)
    print("🔄 ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ МАТЧЕЙ")
    print("="*80)
    print(f"\n📊 Всего предсказаний: {len(predictions)}")
    
    # Находим предсказания без результатов
    to_update = [p for p in predictions if p.get('was_correct') is None and p.get('home_score') is None]
    
    if not to_update:
        print("\n✅ Все предсказания уже имеют результаты!")
        return
    
    print(f"\n🔄 Обновляем {len(to_update)} матчей...")
    print("-"*80)
    
    updated_count = 0
    correct_count = 0
    
    for pred in to_update:
        match_id = pred.get('match_id')
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        
        print(f"\n📋 {home} vs {away} (ID: {match_id})")
        print(f"   Прогноз: {prob:.1f}% на {minute}'")
        
        # Получаем результат
        home_score, away_score = get_match_result(match_id, home, away, None)
        
        if home_score is not None and away_score is not None:
            total_goals = home_score + away_score
            had_goal = total_goals > 0
            predicted_goal = prob > 46  # порог отправки
            
            was_correct = (had_goal == predicted_goal)
            
            pred['was_correct'] = was_correct
            pred['home_score'] = home_score
            pred['away_score'] = away_score
            
            updated_count += 1
            if was_correct:
                correct_count += 1
                print(f"   ✅ ПРОГНОЗ СБЫЛСЯ! ({home_score}:{away_score})")
            else:
                print(f"   ❌ ПРОГНОЗ НЕ СБЫЛСЯ ({home_score}:{away_score})")
        else:
            print(f"   ⚠️ Результат не найден")
    
    # Обновляем статистику
    total = len(predictions)
    stats['total_predictions'] = total
    stats['correct_predictions'] = correct_count
    stats['incorrect_predictions'] = total - correct_count
    stats['accuracy_rate'] = correct_count / total if total > 0 else 0
    
    # Обновляем статистику по уверенности
    stats['by_confidence'] = {}
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
    
    print("\n" + "="*80)
    print("📊 ОБНОВЛЕННАЯ СТАТИСТИКА:")
    print("="*80)
    print(f"  Обновлено матчей: {updated_count}")
    print(f"  Всего предсказаний: {total}")
    print(f"  ✅ Сбылось: {correct_count}")
    print(f"  ❌ Не сбылось: {total - correct_count}")
    print(f"  🎯 Точность: {correct_count/total*100:.1f}%")
    
    # Показываем по уровням
    print("\n📊 ПО УРОВНЯМ УВЕРЕННОСТИ:")
    for conf, data in stats['by_confidence'].items():
        acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        print(f"  {conf}: {data['total']} прогнозов, точность {acc:.1f}%")

if __name__ == "__main__":
    update_predictions()