# find_understat_ids_fixed.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
import random

async def fetch_with_headers(url, session):
    """Запрос с правильными заголовками"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"  ❌ Статус {response.status} для {url}")
                return None
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return None

async def find_match_ids():
    """Ищет реальные ID матчей на Understat"""
    
    print("🔍 Поиск реальных ID матчей на Understat...")
    print("=" * 60)
    
    conn = aiohttp.TCPConnector(ssl=False)  # Отключаем SSL для теста
    async with aiohttp.ClientSession(connector=conn) as session:
        # Проверим главные лиги
        leagues = [
            ('EPL', 'https://understat.com/league/EPL'),
            ('La_liga', 'https://understat.com/league/La_liga'),
            ('Bundesliga', 'https://understat.com/league/Bundesliga'),
            ('Serie_A', 'https://understat.com/league/Serie_A'),
            ('Ligue_1', 'https://understat.com/league/Ligue_1')
        ]
        
        all_matches = []
        
        for league_name, url in leagues:
            print(f"\n📊 Лига: {league_name}")
            print(f"URL: {url}")
            
            # Добавляем случайную задержку
            await asyncio.sleep(random.uniform(1, 3))
            
            html = await fetch_with_headers(url, session)
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем скрипт с данными
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'datesData' in script.string:
                    # Несколько вариантов паттернов
                    patterns = [
                        r'var datesData\s*=\s*(\[.+?\]);',
                        r'datesData\s*=\s*(\[.+?\]);',
                        r'JSON\.parse\(\'(.+?)\'\)'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script.string, re.DOTALL)
                        if match:
                            try:
                                data_str = match.group(1)
                                # Если это JSON в строке, нужно декодировать
                                if '\\' in data_str:
                                    data_str = data_str.encode('utf-8').decode('unicode_escape')
                                
                                data = json.loads(data_str)
                                
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
                                for match in match_ids[:5]:
                                    print(f"     • ID {match['id']}: {match['home']} vs {match['away']} ({match['date']})")
                                
                                all_matches.extend(match_ids)
                                break
                                
                            except json.JSONDecodeError as e:
                                print(f"  ⚠️ Ошибка парсинга JSON: {e}")
                                continue
        
        print("\n" + "=" * 60)
        print(f"📊 Всего найдено матчей: {len(all_matches)}")
        
        # Сохраняем в файл
        if all_matches:
            with open('understat_matches.json', 'w', encoding='utf-8') as f:
                json.dump(all_matches, f, ensure_ascii=False, indent=2)
            print("✅ Результаты сохранены в understat_matches.json")

if __name__ == "__main__":
    asyncio.run(find_match_ids())