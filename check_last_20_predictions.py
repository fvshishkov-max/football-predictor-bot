# check_last_20_predictions.py
"""
Проверка последних 20 прогнозов и их результатов
Запуск: python check_last_20_predictions.py
"""

import json
import os
import requests
from datetime import datetime, timedelta
import config

def get_match_result_from_api(match_id, home_team, away_team):
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
        print(f"  API ошибка: {e}")
    
    return None, None

def check_predictions():
    """Проверяет последние 20 предсказаний"""
    
    pred_file = 'data/predictions/predictions.json'
    
    if not os.path.exists(pred_file):
        print("❌ Файл с предсказаниями не найден!")
        return
    
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print("="*80)
    print("📊 ПРОВЕРКА ПОСЛЕДНИХ 20 ПРОГНОЗОВ")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Берем последние 20
    last_20 = predictions[-20:] if len(predictions) >= 20 else predictions
    
    print(f"\n📈 Всего предсказаний: {len(predictions)}")
    print(f"🔍 Проверяем: {len(last_20)} последних")
    print("-"*80)
    
    updated = 0
    correct = 0
    incorrect = 0
    pending = 0
    
    for i, pred in enumerate(last_20, 1):
        match_id = pred.get('match_id')
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0) * 100
        conf = pred.get('confidence_level', 'UNKNOWN')
        timestamp = pred.get('timestamp', '')[:19]
        was_correct = pred.get('was_correct')
        home_score = pred.get('home_score')
        away_score = pred.get('away_score')
        
        # Проверяем, есть ли результат
        if was_correct is None or home_score is None:
            # Пытаемся получить результат из API
            api_home, api_away = get_match_result_from_api(match_id, home, away)
            
            if api_home is not None and api_away is not None:
                total_goals = api_home + api_away
                had_goal = total_goals > 0
                predicted_goal = prob > 46
                
                was_correct = (had_goal == predicted_goal)
                home_score = api_home
                away_score = api_away
                
                # Обновляем в памяти
                pred['was_correct'] = was_correct
                pred['home_score'] = home_score
                pred['away_score'] = away_score
                updated += 1
            else:
                pending += 1
        else:
            correct += 1 if was_correct else 0
            incorrect += 0 if was_correct else 1
        
        # Определяем статус
        if was_correct is True:
            status = "✅ СБЫЛСЯ"
            status_color = "🟢"
        elif was_correct is False:
            status = "❌ НЕ СБЫЛСЯ"
            status_color = "🔴"
        else:
            status = "⏳ ОЖИДАНИЕ"
            status_color = "🟡"
        
        # Показываем результат
        print(f"\n{i:2d}. {timestamp} | {status_color} {status}")
        print(f"    🏟 {home} vs {away}")
        print(f"    ⏱ {minute}' | 📊 {prob:.1f}% | 🎯 {conf}")
        
        if home_score is not None and away_score is not None:
            total = home_score + away_score
            print(f"    📊 Результат: {home_score}:{away_score} (всего голов: {total})")
            print(f"    🎯 Прогноз: {'Будет гол' if prob > 46 else 'Не будет гола'}")
            print(f"    📌 Факт: {'Гол был' if total > 0 else 'Гола не было'}")
        else:
            print(f"    📌 Результат пока неизвестен")
    
    print("\n" + "="*80)
    print("📊 СТАТИСТИКА ПО 20 ПОСЛЕДНИМ:")
    print("="*80)
    print(f"  ✅ Сбылось: {correct}")
    print(f"  ❌ Не сбылось: {incorrect}")
    print(f"  ⏳ Ожидают результата: {pending}")
    print(f"  🎯 Точность: {correct/(correct+incorrect)*100:.1f}%" if (correct+incorrect) > 0 else "  🎯 Нет данных")
    
    print("\n" + "="*80)
    print("📊 ОБЩАЯ СТАТИСТИКА:")
    print("="*80)
    print(f"  Всего предсказаний: {stats.get('total_predictions', 0)}")
    print(f"  Правильных: {stats.get('correct_predictions', 0)}")
    print(f"  Неправильных: {stats.get('incorrect_predictions', 0)}")
    print(f"  Точность: {stats.get('accuracy_rate', 0)*100:.1f}%")
    print(f"  Сигналов отправлено: {stats.get('signals_sent_46plus', 0)}")
    
    # Сохраняем обновленные данные
    if updated > 0:
        with open(pred_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n✅ Обновлено {updated} предсказаний с результатами из API")
    
    # Показываем последние сигналы
    signals = [p for p in predictions if p.get('signal')]
    if signals:
        print("\n" + "="*80)
        print("🔔 ПОСЛЕДНИЕ 5 СИГНАЛОВ:")
        print("="*80)
        for sig in signals[-5:]:
            home = sig.get('home_team', '?')
            away = sig.get('away_team', '?')
            prob = sig.get('goal_probability', 0) * 100
            conf = sig.get('confidence_level', '?')
            minute = sig.get('minute', 0)
            was_correct = sig.get('was_correct')
            status = "✅" if was_correct else ("❌" if was_correct is False else "⏳")
            print(f"  {status} {home} vs {away} ({minute}') - {prob:.1f}% ({conf})")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_predictions()