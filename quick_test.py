# quick_test.py
"""
Быстрый тест API - проверяет, возвращает ли API live матчи
"""

import requests
import config
import time

def test_api():
    print("="*60)
    print("БЫСТРЫЙ ТЕСТ API")
    print("="*60)
    
    url = "https://api.sstats.net/Games/list"
    params = {'apikey': config.SSTATS_TOKEN, 'Live': 'true', 'Limit': 10}
    
    for i in range(5):
        print(f"\nЗапрос {i+1}:")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            games = data.get('data', [])
            print(f"  Статус: 200, Матчей: {len(games)}")
            if games:
                for game in games[:3]:
                    home = game.get('homeTeam', {}).get('name', '?')
                    away = game.get('awayTeam', {}).get('name', '?')
                    minute = game.get('elapsed', 0)
                    print(f"    • {home} vs {away} ({minute}')")
        else:
            print(f"  Ошибка: {response.status_code}")
        
        time.sleep(3)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_api()