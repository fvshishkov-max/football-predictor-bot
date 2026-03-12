import asyncio
import logging
from api_client import SStatsClient
import config

logging.basicConfig(level=logging.INFO)

async def test_api():
    print("🔍 Тестирование SStats API (исправленная версия)...")
    
    client = SStatsClient(config.SSTATS_API_KEY)
    
    # Тест 1: Получение LIVE матчей
    print("\n1. Получение LIVE матчей...")
    live_matches = await client.get_live_matches()
    print(f"   Найдено LIVE матчей: {len(live_matches)}")
    
    if live_matches:
        match = live_matches[0]
        print(f"   Пример: {match.home_team.name} vs {match.away_team.name} [{match.home_score}:{match.away_score}]")
        
        # Тест 2: Получение статистики
        print(f"\n2. Получение статистики для матча {match.id}...")
        stats = await client.get_match_statistics(match.id)
        print(f"   Статистика: {'получена' if stats else 'не найдена'}")
        
        # Тест 3: Получение событий
        print(f"\n3. Получение событий для матча {match.id}...")
        events = await client.get_match_events(match.id)
        print(f"   Событий: {len(events)}")
    
    # Тест 4: Получение всех матчей на сегодня
    print("\n4. Получение всех матчей на сегодня...")
    today_matches = await client.get_today_matches()
    print(f"   Найдено матчей на сегодня: {len(today_matches)}")
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_api())