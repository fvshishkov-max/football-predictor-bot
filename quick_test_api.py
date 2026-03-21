# quick_test_api.py
"""
Быстрый тест API для проверки наличия матчей
"""

import asyncio
from api_client import UnifiedFastClient
import config

async def test():
    print("="*60)
    print("БЫСТРЫЙ ТЕСТ API")
    print("="*60)
    
    client = UnifiedFastClient()
    
    print("\n1. Получение live матчей...")
    matches = await client.get_live_matches()
    
    print(f"\n2. Результат: {len(matches)} live матчей")
    
    if matches:
        print("\n3. Первые 5 матчей:")
        for m in matches[:5]:
            home = m.home_team.name if m.home_team else "?"
            away = m.away_team.name if m.away_team else "?"
            minute = m.minute or 0
            print(f"   {home} vs {away} ({minute}')")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())