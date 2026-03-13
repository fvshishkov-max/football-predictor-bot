# test_xg_football_data.py
import asyncio
import logging
from datetime import datetime, timedelta
from xg_manager import XGManager
from models import Team, Match, LiveStats
import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_football_data_xg():
    """Тестирует xG через football-data.org"""
    
    print("🔍 Тестирование football-data.org xG провайдера...")
    print("-" * 60)
    
    xg_manager = XGManager(config.FOOTBALL_DATA_API_KEY)
    
    # Тестовые матчи
    test_matches = [
        {
            'name': 'Manchester City vs Liverpool',
            'home': 'Manchester City',
            'away': 'Liverpool',
            'league_id': 2,  # Premier League
            'date': datetime.now() - timedelta(days=7)
        },
        {
            'name': 'Real Madrid vs Barcelona',
            'home': 'Real Madrid',
            'away': 'Barcelona',
            'league_id': 4,  # La Liga
            'date': datetime.now() - timedelta(days=14)
        }
    ]
    
    for i, test in enumerate(test_matches, 1):
        print(f"\n📊 Тест {i}: {test['name']}")
        print(f"   Команды: {test['home']} vs {test['away']}")
        print(f"   Лига ID: {test['league_id']}")
        print(f"   Дата: {test['date'].strftime('%Y-%m-%d')}")
        
        xg_data = await xg_manager.get_xg(
            match_id=i,
            home_team=test['home'],
            away_team=test['away'],
            league_id=test['league_id'],
            match_date=test['date']
        )
        
        if xg_data:
            print(f"   ✅ xG получен!")
            print(f"   • xG дома: {xg_data.home_xg:.2f}")
            print(f"   • xG в гостях: {xg_data.away_xg:.2f}")
            print(f"   • Всего xG: {xg_data.total_xg:.2f}")
            print(f"   • Источник: {xg_data.source}")
        else:
            print(f"   ❌ xG не найден")
        
        # Статистика после каждого запроса
        stats = xg_manager.get_stats()
        print(f"\n📈 Статистика:")
        print(f"   • Осталось запросов: {stats.get('rate_limit_remaining', 'N/A')}")
    
    await xg_manager.close()

async def main():
    print("🚀 Тестирование football-data.org xG провайдера")
    print("=" * 60)
    await test_football_data_xg()
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main())