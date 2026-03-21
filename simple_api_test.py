# simple_api_test.py
import requests
import config

print("="*60)
print("ТЕСТ SSTATS API")
print("="*60)

# Получаем live матчи
url = "https://api.sstats.net/Games/list"
params = {
    'apikey': config.SSTATS_TOKEN,
    'Live': 'true',
    'Limit': 5
}

print("\n1. Получение live матчей...")
response = requests.get(url, params=params, timeout=10)

if response.status_code != 200:
    print(f"❌ Ошибка: {response.status_code}")
    print(f"   {response.text[:200]}")
    exit()

data = response.json()
games = data.get('data', [])
print(f"✅ Найдено live матчей: {len(games)}")

if not games:
    print("❌ Нет live матчей для теста")
    exit()

# Ищем матч со статистикой
print("\n2. Поиск матча со статистикой...")
found = False

for game in games:
    game_id = game.get('id')
    home = game.get('homeTeam', {}).get('name', '?')
    away = game.get('awayTeam', {}).get('name', '?')
    minute = game.get('elapsed', 0)
    
    print(f"\n   Проверка: {home} vs {away} (ID: {game_id}, {minute}')")
    
    detail_url = f"https://api.sstats.net/Games/{game_id}"
    detail_params = {'apikey': config.SSTATS_TOKEN}
    detail_response = requests.get(detail_url, params=detail_params, timeout=10)
    
    if detail_response.status_code != 200:
        print(f"      ❌ Ошибка получения статистики")
        continue
    
    detail_data = detail_response.json()
    stats = detail_data.get('data', {}).get('statistics')
    
    if not stats:
        print(f"      ❌ Нет статистики")
        continue
    
    home_stats = stats.get('homeStats', {})
    away_stats = stats.get('awayStats', {})
    other_home = stats.get('otherStatsHome', {}) or {}
    other_away = stats.get('otherStatsAway', {}) or {}
    
    shots_home = home_stats.get('Total Shots', 0) or 0
    shots_away = away_stats.get('Total Shots', 0) or 0
    shots_on_target_home = home_stats.get('Shots on Goal', 0) or 0
    shots_on_target_away = away_stats.get('Shots on Goal', 0) or 0
    possession_home = home_stats.get('Ball Possession', 50)
    possession_away = away_stats.get('Ball Possession', 50)
    corners_home = home_stats.get('Corner Kicks', 0) or 0
    corners_away = away_stats.get('Corner Kicks', 0) or 0
    xg_home = other_home.get('Expected goals (xG)', 0.5) if other_home else 0.5
    xg_away = other_away.get('Expected goals (xG)', 0.5) if other_away else 0.5
    
    if shots_home > 0 or shots_away > 0 or shots_on_target_home > 0 or shots_on_target_away > 0:
        found = True
        print(f"\n✅ НАЙДЕН МАТЧ СО СТАТИСТИКОЙ!")
        print(f"\n📋 {home} vs {away} ({minute}')")
        print("\n📊 СТАТИСТИКА:")
        print(f"   Удары: {shots_home} : {shots_away}")
        print(f"   Удары в створ: {shots_on_target_home} : {shots_on_target_away}")
        print(f"   Владение: {possession_home}% : {possession_away}%")
        print(f"   Угловые: {corners_home} : {corners_away}")
        print(f"   xG: {xg_home} : {xg_away}")
        break

if not found:
    print("\n❌ Не найден матч со статистикой")
    print("   Возможные причины:")
    print("   1. Все матчи только начались (первые 10-15 минут)")
    print("   2. API не возвращает статистику для этих лиг")
    print("   3. Нужно подождать накопления статистики")

print("\n" + "="*60)