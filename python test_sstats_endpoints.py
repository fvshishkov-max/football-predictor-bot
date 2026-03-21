python -c "
import requests
import config

print('='*60)
print('ПРОВЕРКА SSTATS API')
print('='*60)

# Получаем live матчи
url = 'https://api.sstats.net/Games/list'
params = {'apikey': config.SSTATS_TOKEN, 'Live': 'true', 'Limit': 3}
response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()
    games = data.get('data', [])
    print(f'Найдено live матчей: {len(games)}')
    
    if games:
        game = games[0]
        game_id = game.get('id')
        home = game.get('homeTeam', {}).get('name', '?')
        away = game.get('awayTeam', {}).get('name', '?')
        minute = game.get('elapsed', 0)
        print(f'\nМатч: {home} vs {away} (ID: {game_id}, {minute}\')')
        
        # Получаем статистику
        detail_url = f'https://api.sstats.net/Games/{game_id}'
        detail_params = {'apikey': config.SSTATS_TOKEN}
        detail_response = requests.get(detail_url, params=detail_params, timeout=10)
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            stats = detail_data.get('data', {}).get('statistics')
            
            if stats:
                home_stats = stats.get('homeStats', {})
                away_stats = stats.get('awayStats', {})
                other_home = stats.get('otherStatsHome', {})
                other_away = stats.get('otherStatsAway', {})
                
                print('\n📊 СТАТИСТИКА:')
                print(f'  Удары: {home_stats.get(\"Total Shots\", 0)} : {away_stats.get(\"Total Shots\", 0)}')
                print(f'  В створ: {home_stats.get(\"Shots on Goal\", 0)} : {away_stats.get(\"Shots on Goal\", 0)}')
                print(f'  Владение: {home_stats.get(\"Ball Possession\", 50)}% : {away_stats.get(\"Ball Possession\", 50)}%')
                print(f'  Угловые: {home_stats.get(\"Corner Kicks\", 0)} : {away_stats.get(\"Corner Kicks\", 0)}')
                print(f'  xG: {other_home.get(\"Expected goals (xG)\", 0.5)} : {other_away.get(\"Expected goals (xG)\", 0.5)}')
            else:
                print('❌ Нет статистики для этого матча')
        else:
            print(f'❌ Ошибка получения статистики: {detail_response.status_code}')
    else:
        print('❌ Нет live матчей')
else:
    print(f'❌ Ошибка: {response.status_code}')

print('\n' + '='*60)
"