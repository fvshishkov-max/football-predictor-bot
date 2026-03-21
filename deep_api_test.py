# deep_api_test.py
"""
Глубокий тест всех API с полным анализом доступных данных
"""

import requests
import json
import config
from datetime import datetime

def test_sstats_api():
    """Глубокий тест SStats API"""
    print("\n" + "="*80)
    print("🔵 SSTATS API - ГЛУБОКИЙ ТЕСТ")
    print("="*80)
    
    results = {
        'name': 'SStats API',
        'working': False,
        'endpoints': {},
        'statistics': {}
    }
    
    # 1. Тест получения live матчей
    print("\n1.1 Получение live матчей:")
    print("-"*40)
    
    url = "https://api.sstats.net/Games/list"
    params = {'apikey': config.SSTATS_TOKEN, 'Live': 'true', 'Limit': 10}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            games = data.get('data', [])
            print(f"✅ Найдено live матчей: {len(games)}")
            results['working'] = True
            results['endpoints']['list'] = {'status': 'ok', 'count': len(games)}
            
            if games:
                # Берем первый матч для детального анализа
                game = games[0]
                game_id = game.get('id')
                home = game.get('homeTeam', {}).get('name', '?')
                away = game.get('awayTeam', {}).get('name', '?')
                minute = game.get('elapsed', 0)
                score = f"{game.get('homeResult', 0)}:{game.get('awayResult', 0)}"
                
                print(f"\n   Тестовый матч: {home} vs {away}")
                print(f"   ID: {game_id}, Минута: {minute}', Счет: {score}")
                results['test_match'] = {'id': game_id, 'home': home, 'away': away, 'minute': minute}
                
                # 2. Получение детальной статистики
                print("\n1.2 Получение детальной статистики матча:")
                print("-"*40)
                
                detail_url = f"https://api.sstats.net/Games/{game_id}"
                detail_params = {'apikey': config.SSTATS_TOKEN}
                detail_response = requests.get(detail_url, params=detail_params, timeout=15)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    stats = detail_data.get('data', {}).get('statistics')
                    
                    if stats:
                        print("✅ Статистика найдена!")
                        
                        home_stats = stats.get('homeStats', {})
                        away_stats = stats.get('awayStats', {})
                        other_home = stats.get('otherStatsHome', {}) or {}
                        other_away = stats.get('otherStatsAway', {}) or {}
                        
                        # Собираем все доступные поля
                        all_fields = set()
                        all_fields.update(home_stats.keys())
                        all_fields.update(away_stats.keys())
                        all_fields.update(other_home.keys())
                        all_fields.update(other_away.keys())
                        
                        print(f"\n   📊 ДОСТУПНЫЕ ПОЛЯ СТАТИСТИКИ ({len(all_fields)}):")
                        for field in sorted(all_fields):
                            home_val = home_stats.get(field, '—')
                            away_val = away_stats.get(field, '—')
                            if field in other_home:
                                home_val = other_home.get(field, '—')
                            if field in other_away:
                                away_val = other_away.get(field, '—')
                            print(f"      {field}: {home_val} : {away_val}")
                        
                        results['statistics'] = {
                            'fields': list(all_fields),
                            'has_shots': 'Total Shots' in home_stats,
                            'has_shots_on_target': 'Shots on Goal' in home_stats,
                            'has_possession': 'Ball Possession' in home_stats,
                            'has_corners': 'Corner Kicks' in home_stats,
                            'has_xg': any('xG' in f or 'Expected' in f for f in all_fields)
                        }
                    else:
                        print("❌ Нет статистики для этого матча")
                else:
                    print(f"❌ Ошибка: {detail_response.status_code}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return results

def test_rapidapi():
    """Глубокий тест RapidAPI (api-football.com)"""
    print("\n" + "="*80)
    print("🟢 RAPIDAPI (api-football.com) - ГЛУБОКИЙ ТЕСТ")
    print("="*80)
    
    results = {
        'name': 'RapidAPI',
        'working': False,
        'endpoints': {},
        'statistics': {}
    }
    
    headers = {
        'X-RapidAPI-Key': config.RAPIDAPI_KEY,
        'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
    }
    
    # 1. Проверка статуса API
    print("\n2.1 Проверка статуса API:")
    print("-"*40)
    
    try:
        response = requests.get("https://api-football-v1.p.rapidapi.com/v3/status", headers=headers, timeout=15)
        if response.status_code == 200:
            print("✅ API доступен")
            results['working'] = True
        else:
            print(f"⚠️ Статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return results
    
    # 2. Получение live матчей
    print("\n2.2 Получение live матчей:")
    print("-"*40)
    
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {'live': 'all'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            print(f"✅ Найдено live матчей: {len(fixtures)}")
            results['endpoints']['list'] = {'status': 'ok', 'count': len(fixtures)}
            
            if fixtures:
                fixture = fixtures[0]
                fixture_id = fixture.get('fixture', {}).get('id')
                home = fixture.get('teams', {}).get('home', {}).get('name', '?')
                away = fixture.get('teams', {}).get('away', {}).get('name', '?')
                minute = fixture.get('fixture', {}).get('status', {}).get('elapsed', 0)
                score_home = fixture.get('goals', {}).get('home', 0)
                score_away = fixture.get('goals', {}).get('away', 0)
                
                print(f"\n   Тестовый матч: {home} vs {away}")
                print(f"   ID: {fixture_id}, Минута: {minute}', Счет: {score_home}:{score_away}")
                results['test_match'] = {'id': fixture_id, 'home': home, 'away': away, 'minute': minute}
                
                # 3. Получение статистики
                print("\n2.3 Получение статистики матча:")
                print("-"*40)
                
                stat_url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics"
                stat_params = {'fixture': fixture_id}
                stat_response = requests.get(stat_url, headers=headers, params=stat_params, timeout=15)
                
                if stat_response.status_code == 200:
                    stat_data = stat_response.json()
                    stats = stat_data.get('response', [])
                    
                    if stats:
                        print("✅ Статистика найдена!")
                        
                        all_stats = {}
                        for team_stats in stats:
                            team = team_stats.get('team', {}).get('name', '')
                            is_home = 'home' in team.lower()
                            
                            for stat in team_stats.get('statistics', []):
                                stat_type = stat.get('type', '')
                                value = stat.get('value', 0)
                                if value is None:
                                    value = 0
                                
                                if is_home:
                                    all_stats[f'{stat_type}_home'] = value
                                else:
                                    all_stats[f'{stat_type}_away'] = value
                        
                        print(f"\n   📊 ДОСТУПНЫЕ ПОЛЯ СТАТИСТИКИ:")
                        for key in sorted(all_stats.keys()):
                            print(f"      {key}: {all_stats[key]}")
                        
                        results['statistics'] = {
                            'fields': list(all_stats.keys()),
                            'has_shots': any('Shots' in k for k in all_stats.keys()),
                            'has_shots_on_target': any('Shots on Goal' in k for k in all_stats.keys()),
                            'has_possession': any('Possession' in k for k in all_stats.keys()),
                            'has_corners': any('Corner' in k for k in all_stats.keys()),
                            'has_xg': any('xG' in k for k in all_stats.keys())
                        }
                    else:
                        print("❌ Нет статистики для этого матча")
                else:
                    print(f"❌ Ошибка: {stat_response.status_code}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return results

def test_odds_api():
    """Тест Odds-API.io"""
    print("\n" + "="*80)
    print("🟡 ODDS-API.IO - ГЛУБОКИЙ ТЕСТ")
    print("="*80)
    
    results = {
        'name': 'Odds-API',
        'working': False,
        'endpoints': {},
        'statistics': {}
    }
    
    api_key = "dc4a34c30f63bf408f6ef335db7da322f69c4f5d6dab99dd7e2767df8313948e"
    
    # 1. Получение списка видов спорта
    print("\n3.1 Получение списка видов спорта:")
    print("-"*40)
    
    try:
        url = "https://api.odds-api.io/v4/sports"
        params = {'api_key': api_key}
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Найдено видов спорта: {len(data)}")
            results['working'] = True
            
            # Находим футбол
            soccer = [s for s in data if 'soccer' in s.get('key', '')]
            print(f"   Футбольные лиги: {len(soccer)}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 2. Получение live матчей
    print("\n3.2 Получение live матчей:")
    print("-"*40)
    
    try:
        url = "https://api.odds-api.io/v4/sports/soccer/odds"
        params = {
            'api_key': api_key,
            'region': 'eu',
            'markets': 'h2h',
            'dateFormat': 'iso'
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Найдено матчей: {len(data)}")
            
            if data:
                match = data[0]
                print(f"\n   Тестовый матч: {match.get('home_team')} vs {match.get('away_team')}")
                print(f"   ID: {match.get('id')}")
                print(f"   Время: {match.get('commence_time', '')[:19]}")
                
                # Odds-API не предоставляет статистику
                print("\n3.3 Проверка наличия статистики:")
                print("-"*40)
                print("⚠️ Odds-API НЕ ПРЕДОСТАВЛЯЕТ СТАТИСТИКУ")
                print("   Доступны только коэффициенты и информация о матчах")
                
                results['statistics'] = {
                    'has_stats': False,
                    'note': 'Только коэффициенты'
                }
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return results

def test_football_data():
    """Тест Football-Data.org"""
    print("\n" + "="*80)
    print("🟠 FOOTBALL-DATA.ORG - ГЛУБОКИЙ ТЕСТ")
    print("="*80)
    
    results = {
        'name': 'Football-Data.org',
        'working': False,
        'endpoints': {},
        'statistics': {}
    }
    
    headers = {'X-Auth-Token': config.FOOTBALL_DATA_KEY}
    
    # 1. Получение live матчей
    print("\n4.1 Получение live матчей:")
    print("-"*40)
    
    try:
        url = "https://api.football-data.org/v4/matches"
        params = {'status': 'LIVE'}
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            print(f"✅ Найдено live матчей: {len(matches)}")
            results['working'] = True
            
            if matches:
                match = matches[0]
                match_id = match.get('id')
                home = match.get('homeTeam', {}).get('name', '?')
                away = match.get('awayTeam', {}).get('name', '?')
                minute = match.get('minute', 0)
                
                print(f"\n   Тестовый матч: {home} vs {away}")
                print(f"   ID: {match_id}, Минута: {minute}'")
                
                # 2. Получение статистики
                print("\n4.2 Получение статистики матча:")
                print("-"*40)
                
                stat_url = f"https://api.football-data.org/v4/matches/{match_id}/statistics"
                stat_response = requests.get(stat_url, headers=headers, timeout=15)
                
                if stat_response.status_code == 200:
                    stat_data = stat_response.json()
                    print("✅ Статистика найдена!")
                    results['statistics']['has_stats'] = True
                else:
                    print(f"❌ Статистика не доступна: {stat_response.status_code}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return results

def print_summary(results):
    """Выводит сводку результатов"""
    print("\n" + "="*80)
    print("📊 СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("="*80)
    
    print("\n| API | Работает | Статистика | xG | Примечание |")
    print("|-----|----------|------------|----|------------|")
    
    for r in results:
        name = r['name']
        working = "✅" if r['working'] else "❌"
        has_stats = "✅" if r.get('statistics', {}).get('has_stats') or r.get('statistics', {}).get('fields') else "❌"
        has_xg = "✅" if r.get('statistics', {}).get('has_xg') else "❌"
        note = r.get('statistics', {}).get('note', '')
        
        # Детали статистики
        if r.get('statistics', {}).get('fields'):
            fields = r['statistics']['fields']
            if len(fields) > 5:
                note = f"{len(fields)} полей"
            else:
                note = ", ".join(fields[:3])
        
        print(f"| {name} | {working} | {has_stats} | {has_xg} | {note} |")
    
    print("\n" + "="*80)
    print("💡 РЕКОМЕНДАЦИЯ:")
    print("="*80)
    
    # Определяем лучший API
    best_api = None
    for r in results:
        if r['working'] and r.get('statistics', {}).get('fields'):
            if not best_api or len(r['statistics']['fields']) > len(best_api.get('statistics', {}).get('fields', [])):
                best_api = r
    
    if best_api:
        print(f"\n✅ Рекомендуется использовать: {best_api['name']}")
        print(f"   • Предоставляет {len(best_api['statistics'].get('fields', []))} полей статистики")
        if best_api['statistics'].get('has_xg'):
            print("   • Включает xG (ожидаемые голы)")
    else:
        print("\n⚠️ Ни один API не предоставляет статистику")
        print("   Рекомендуется:")
        print("   1. Проверить API ключи")
        print("   2. Дождаться live матчей со статистикой")
        print("   3. Использовать SStats API для xG")

if __name__ == "__main__":
    print("="*80)
    print("🔍 ГЛУБОКИЙ ТЕСТ ВСЕХ API")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Тестируем все API
    results.append(test_sstats_api())
    results.append(test_rapidapi())
    results.append(test_odds_api())
    results.append(test_football_data())
    
    # Выводим сводку
    print_summary(results)