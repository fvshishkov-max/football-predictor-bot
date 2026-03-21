# auto_update_results.py
"""
Автоматическое обновление результатов матчей через API
Запуск: python auto_update_results.py
"""

import json
import requests
import sqlite3
import os
from datetime import datetime, timedelta
import time

# Импортируем конфигурацию
import config

def get_match_result_from_api(match_id, home_team, away_team):
    """
    Получает результат матча из API
    Пробует разные источники
    """
    
    # 1. Пробуем SStats API
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
        print(f"  SStats API ошибка: {e}")
    
    # 2. Пробуем Football-Data.org
    try:
        url = f"https://api.football-data.org/v4/matches/{match_id}"
        headers = {'X-Auth-Token': config.FOOTBALL_DATA_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            home_score = data.get('score', {}).get('fullTime', {}).get('home')
            away_score = data.get('score', {}).get('fullTime', {}).get('away')
            
            if home_score is not None and away_score is not None:
                return home_score, away_score
    except Exception as e:
        print(f"  Football-Data API ошибка: {e}")
    
    # 3. Пробуем RapidAPI (api-football.com)
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        querystring = {"id": str(match_id)}
        headers = {
            "X-RapidAPI-Key": config.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('response'):
                fixture = data['response'][0]
                goals = fixture.get('goals', {})
                home_score = goals.get('home')
                away_score = goals.get('away')
                
                if home_score is not None and away_score is not None:
                    return home_score, away_score
    except Exception as e:
        print(f"  RapidAPI ошибка: {e}")
    
    return None, None

def update_predictions_auto():
    """Автоматически обновляет результаты предсказаний"""
    
    print("="*70)
    print("⚽ АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*70)
    
    # Загружаем предсказания
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    stats = data.get('accuracy_stats', {})
    
    print(f"\n📊 Всего предсказаний: {len(predictions)}")
    
    # Находим предсказания без результатов
    to_update = [p for p in predictions if p.get('was_correct') is None]
    
    if not to_update:
        print("\n✅ Все предсказания уже имеют результаты!")
        return
    
    print(f"\n🔄 Обновляем {len(to_update)} матчей...")
    print("-"*70)
    
    updated_count = 0
    correct_count = 0
    
    for pred in to_update:
        match_id = pred.get('match_id')
        home = pred.get('home_team', 'Unknown')
        away = pred.get('away_team', 'Unknown')
        prob = pred.get('goal_probability', 0) * 100
        minute = pred.get('minute', 0)
        
        print(f"\n🏟 {home} vs {away} (ID: {match_id})")
        print(f"   ⏱ {minute}' | 📊 {prob:.1f}%")
        
        # Получаем результат из API
        home_score, away_score = get_match_result_from_api(match_id, home, away)
        
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
            print(f"   ⚠️ Результат не найден в API")
            # Оставляем как есть для ручного ввода позже
    
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
    
    print("\n" + "="*70)
    print("📊 ОБНОВЛЕННАЯ СТАТИСТИКА:")
    print("-"*70)
    print(f"  Обновлено матчей: {updated_count}")
    print(f"  Всего предсказаний: {total}")
    print(f"  ✅ Сбылось: {correct_count}")
    print(f"  ❌ Не сбылось: {total - correct_count}")
    print(f"  🎯 Точность: {correct_count/total*100:.1f}%")
    print("="*70)
    
    # Сохраняем лог обновления
    with open('data/logs/update_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Обновлено {updated_count} матчей, точность {correct_count/total*100:.1f}%\n")

def update_from_db():
    """Обновляет результаты из локальной базы данных"""
    
    db_path = 'data/history/matches_history.db'
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*70)
    print("📊 ОБНОВЛЕНИЕ ИЗ ЛОКАЛЬНОЙ БАЗЫ ДАННЫХ")
    print("="*70)
    
    # Загружаем предсказания
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    updated_count = 0
    correct_count = 0
    
    for pred in predictions:
        if pred.get('was_correct') is not None:
            continue
        
        match_id = pred.get('match_id')
        
        try:
            cursor.execute(
                "SELECT home_score, away_score FROM matches WHERE match_id = ?",
                (match_id,)
            )
            result = cursor.fetchone()
            
            if result:
                home_score, away_score = result
                total_goals = home_score + away_score
                had_goal = total_goals > 0
                prob = pred.get('goal_probability', 0) * 100
                predicted_goal = prob > 46
                
                was_correct = (had_goal == predicted_goal)
                
                pred['was_correct'] = was_correct
                pred['home_score'] = home_score
                pred['away_score'] = away_score
                
                updated_count += 1
                if was_correct:
                    correct_count += 1
        except:
            pass
    
    conn.close()
    
    if updated_count > 0:
        with open('data/predictions/predictions.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        total = len(predictions)
        print(f"\n✅ Обновлено {updated_count} матчей из базы данных")
        print(f"📊 Точность: {correct_count/total*100:.1f}%")
    else:
        print("\n⚠️ Нет новых результатов в базе данных")

if __name__ == "__main__":
    print("\nВыберите источник данных:")
    print("1. API (SStats, Football-Data, RapidAPI)")
    print("2. Локальная база данных (matches_history.db)")
    print("3. Пропустить")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        update_predictions_auto()
    elif choice == '2':
        update_from_db()
    else:
        print("Обновление отменено")