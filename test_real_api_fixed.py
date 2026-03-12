# test_real_api_fixed.py
import asyncio
import logging
from api_client import SStatsClient
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def test():
    print("🔍 Тестируем реальное API...")
    print(f"Используем API ключ: {config.SSTATS_API_KEY[:5]}...")
    
    # Создаем клиент с реальным API
    client = SStatsClient(
        api_key=config.SSTATS_API_KEY,
        use_mock=False  # False = реальный API
    )
    
    # Получаем LIVE матчи
    print("\n1. Получение LIVE матчей...")
    try:
        live = await client.get_live_matches()
        print(f"   ✅ Найдено LIVE матчей: {len(live)}")
        
        for match in live[:3]:  # Покажем первые 3
            print(f"   • {match.home_team.name} vs {match.away_team.name} "
                  f"[{match.home_score}:{match.away_score}] ({match.minute}')")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Получаем матчи на сегодня
    print("\n2. Получение матчей на сегодня...")
    try:
        today = await client.get_today_matches()
        print(f"   ✅ Найдено матчей на сегодня: {len(today)}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test())