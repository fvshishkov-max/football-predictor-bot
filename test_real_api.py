# test_real_api.py
import asyncio
import logging
from api_client import SStatsClient
import config

logging.basicConfig(level=logging.INFO)

async def test_real_api():
    """Тестирует реальное API с правильными заголовками"""
    
    print("🔍 Тестирование реального SStats API...")
    
    # Создаем клиент с выключенным демо-режимом
    client = SStatsClient(
        api_key=config.SSTATS_API_KEY,
        use_mock=False
    )
    
    # Проверяем доступность API
    print("\n1. Проверка доступности API...")
    if client._check_api_available():
        print("   ✅ API доступно")
    else:
        print("   ❌ API недоступно")
        print("   Будет использован демо-режим")
        return
    
    # Получаем LIVE матчи
    print("\n2. Получение LIVE матчей...")
    live_matches = await client.get_live_matches()
    print(f"   Найдено LIVE матчей: {len(live_matches)}")
    
    for match in live_matches[:3]:  # Покажем первые 3
        print(f"   • {match.home_team.name} vs {match.away_team.name} [{match.home_score}:{match.away_score}]")
        
        # Получаем статистику
        stats = await client.get_match_statistics(match.id)
        if stats:
            print(f"     Статистика получена")
        
        # Получаем события
        events = await client.get_match_events(match.id)
        print(f"     Событий: {len(events)}")
    
    # Получаем матчи на сегодня
    print("\n3. Получение матчей на сегодня...")
    today_matches = await client.get_today_matches()
    print(f"   Найдено матчей на сегодня: {len(today_matches)}")
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_real_api())