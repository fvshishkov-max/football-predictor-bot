# detailed_predictions_analysis.py
"""
Детальный анализ прогнозов с разбором по минутам
Запуск: python detailed_predictions_analysis.py
"""

import json
import os
import requests
from datetime import datetime
from collections import defaultdict
import config

def get_match_result_from_api(match_id):
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
            elapsed = game.get('elapsed', 0)
            
            if home_score is not None and away_score is not None:
                return home_score, away_score, elapsed
    except Exception as e:
        pass
    
    return None, None, None

def analyze_predictions(limit=50):
    """Анализирует последние N предсказаний"""
    
    pred_file = 'data/predictions/predictions.json'
    
    if not os.path.exists(pred_file):
        print("❌ Файл с предсказаниями не найден!")
        return
    
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*100)
    print(f"📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПОСЛЕДНИХ {limit} ПРОГНОЗОВ")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # Берем последние limit
    last_n = predictions[-limit:] if len(predictions) >= limit else predictions
    
    print(f"\n📈 Всего предсказаний: {len(predictions)}")
    print(f"🔍 Анализируем: {len(last_n)} последних")
    print("-"*100)
    
    stats = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'by_minute': defaultdict(lambda: {'total': 0, 'correct': 0, 'goals': 0}),
        'signals': []
    }
    
    print(f"{'№':<4} {'Время':<12} {'Статус':<12} {'Минута':<8} {'Счет':<8} {'Гол':<6} {'Прогноз':<10} {'Факт':<10} {'Матч'}")
    print("-"*100)
    
    for i, pred in enumerate(last_n, 1):
        match_id = pred.get('match_id')
        home = pred.get('home_team', '?')
        away = pred.get('away_team', '?')
        minute = pred.get('minute', 0)
        prob = pred.get('goal_probability', 0) * 100
        conf = pred.get('confidence_level', 'UNKNOWN')
        timestamp = pred.get('timestamp', '')[:16]
        was_correct = pred.get('was_correct')
        home_score = pred.get('home_score')
        away_score = pred.get('away_score')
        is_signal = pred.get('signal') is not None
        
        # Если нет результата, пытаемся получить из API
        if was_correct is None or home_score is None:
            api_home, api_away, api_minute = get_match_result_from_api(match_id)
            if api_home is not None:
                home_score, away_score = api_home, api_away
                total_goals = home_score + away_score
                had_goal = total_goals > 0
                predicted_goal = prob > 46
                was_correct = (had_goal == predicted_goal)
                
                # Обновляем в файле
                pred['was_correct'] = was_correct
                pred['home_score'] = home_score
                pred['away_score'] = away_score
        
        stats['total'] += 1
        
        # Определяем статус
        if was_correct is True:
            status = "✅ СБЫЛСЯ"
            stats['correct'] += 1
            if is_signal:
                stats['by_minute'][minute]['correct'] += 1
                stats['signals'].append({
                    'minute': minute,
                    'home': home,
                    'away': away,
                    'prob': prob,
                    'conf': conf,
                    'result': f"{home_score}:{away_score}"
                })
        elif was_correct is False:
            status = "❌ НЕ СБЫЛСЯ"
            stats['incorrect'] += 1
        else:
            status = "⏳ ОЖИДАНИЕ"
        
        if is_signal:
            stats['by_minute'][minute]['total'] += 1
        
        # Счет
        if home_score is not None and away_score is not None:
            score_str = f"{home_score}:{away_score}"
            total_goals = home_score + away_score
            goal_str = f"{total_goals}"
            fact_str = "ГОЛ" if total_goals > 0 else "НЕТ"
        else:
            score_str = "? : ?"
            goal_str = "?"
            fact_str = "?"
        
        # Прогноз
        pred_str = "ГОЛ" if prob > 46 else "НЕТ"
        
        # Короткое название матча
        match_short = f"{home[:15]} vs {away[:15]}"
        
        print(f"{i:<4} {timestamp:<12} {status:<12} {minute:<8} {score_str:<8} {goal_str:<6} {pred_str:<10} {fact_str:<10} {match_short}")
    
    print("\n" + "="*100)
    print("📊 СТАТИСТИКА ПО ПЕРИОДАМ (СИГНАЛЫ):")
    print("="*100)
    
    periods = {
        '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
        '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
        '90+': (90, 120)
    }
    
    period_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for minute, data in stats['by_minute'].items():
        for period, (start, end) in periods.items():
            if start <= minute < end:
                period_stats[period]['total'] += data['total']
                period_stats[period]['correct'] += data['correct']
                break
    
    print(f"\n{'Период':<10} {'Сигналов':<12} {'Сбылось':<12} {'Точность':<12}")
    print("-"*50)
    
    for period in periods.keys():
        total = period_stats[period]['total']
        correct = period_stats[period]['correct']
        acc = (correct / total * 100) if total > 0 else 0
        bar = '█' * int(acc / 5)
        print(f"{period:<10} {total:<12} {correct:<12} {acc:<11.1f}% {bar}")
    
    print("\n" + "="*100)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("="*100)
    
    total_pred = stats['total']
    correct_pred = stats['correct']
    incorrect_pred = stats['incorrect']
    accuracy = (correct_pred / total_pred * 100) if total_pred > 0 else 0
    
    print(f"\n  ✅ Сбылось: {correct_pred}")
    print(f"  ❌ Не сбылось: {incorrect_pred}")
    print(f"  🎯 Точность: {accuracy:.1f}%")
    
    # Сигналы
    signals = stats['signals']
    if signals:
        print(f"\n🔔 ПОСЛЕДНИЕ 10 СИГНАЛОВ:")
        print("-"*100)
        for sig in signals[-10:]:
            print(f"  {sig['minute']:2d}' | {sig['home'][:20]} vs {sig['away'][:20]} | {sig['prob']:.1f}% ({sig['conf']}) | Результат: {sig['result']}")
    
    # Сохраняем обновления
    with open(pred_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*100)
    
    return stats

def analyze_by_goal_time():
    """Анализ времени голов в сбывшихся прогнозах"""
    
    pred_file = 'data/predictions/predictions.json'
    
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("\n" + "="*100)
    print("⚽ АНАЛИЗ ВРЕМЕНИ ГОЛОВ В СБЫВШИХСЯ ПРОГНОЗАХ")
    print("="*100)
    
    goals_by_minute = defaultdict(int)
    signals_by_minute = defaultdict(int)
    
    for pred in predictions:
        minute = pred.get('minute', 0)
        was_correct = pred.get('was_correct')
        is_signal = pred.get('signal') is not None
        home_score = pred.get('home_score')
        away_score = pred.get('away_score')
        
        if is_signal:
            signals_by_minute[minute] += 1
            
            if was_correct and (home_score is not None and away_score is not None):
                if home_score + away_score > 0:
                    goals_by_minute[minute] += 1
    
    print(f"\n{'Минута':<10} {'Сигналов':<12} {'Голов':<12} {'Эффективность':<15}")
    print("-"*50)
    
    for minute in sorted(goals_by_minute.keys()):
        signals = signals_by_minute[minute]
        goals = goals_by_minute[minute]
        efficiency = (goals / signals * 100) if signals > 0 else 0
        bar = '█' * int(efficiency / 5)
        print(f"{minute:2d}'      {signals:<12} {goals:<12} {efficiency:<14.1f}% {bar}")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    # Анализируем последние 50 прогнозов
    stats = analyze_predictions(50)
    
    # Анализируем время голов
    analyze_by_goal_time()