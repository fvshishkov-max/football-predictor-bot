# find_real_understat_ids.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re

async def find_match_ids():
    """Ищет реальные ID матчей на Understat"""
    
    async with aiohttp.ClientSession() as session:
        # Проверим главные лиги
        leagues = [
            ('EPL', 'https://understat.com/league/EPL'),
            ('La_liga', 'https://understat.com/league/La_liga'),
            ('Bundesliga', 'https://understat.com/league/Bundesliga'),
            ('Serie_A', 'https://understat.com/league/Serie_A'),
            ('Ligue_1', 'https://understat.com/league/Ligue_1')
        ]
        
        print("🔍 Поиск реальных ID матчей на Understat...")
        print("=" * 60)
        
        for league_name, url in leagues:
            print(f"\n📊 Лига: {league_name}")
            print(f"URL: {url}")
            
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"  ❌ Ошибка {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Ищем скрипт с данными
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'datesData' in script.string:
                            match = re.search(r'var datesData\s*=\s*(\[.+?\]);', script.string, re.DOTALL)
                            if match:
                                try:
                                    data = json.loads(match.group(1))
                                    
                                    # Собираем ID матчей
                                    match_ids = []
                                    for day in data[:3]:  # Последние 3 дня
                                        for game in day.get('games', [])[:5]:  # По 5 матчей с каждого дня
                                            match_ids.append({
                                                'id': game.get('id'),
                                                'home': game.get('h'),
                                                'away': game.get('a'),
                                                'date': day.get('date')
                                            })
                                    
                                    print(f"  ✅ Найдено {len(match_ids)} матчей:")
                                    for match in match_ids[:5]:  # Покажем первые 5
                                        print(f"     • ID {match['id']}: {match['home']} vs {match['away']} ({match['date']})")
                                    
                                except json.JSONDecodeError:
                                    pass
                    
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(find_match_ids())