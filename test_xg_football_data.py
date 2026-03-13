# test_xg_football_data.py (обновленная версия)
import asyncio
import logging
from datetime import datetime
from xg_manager import XGManager
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_football_data_xg():
    """Тестирует xG через football-data.org с реальными датами матчей"""
    
    print("🔍 Тестирование football-data.org...")
    print("-" * 60)
    
    xg_manager = XGManager(config.FOOTBALL_DATA_API_KEY)
    
    # Реальные матчи с известными датами (сезон 2023-24)
    test_matches = [
        {
            'name': 'Manchester City vs Liverpool',
            'home': 'Manchester City',
            'away': 'Liverpool',
            'league_id': 2,
            'date': datetime(2024, 3, 10),  # Реальный матч АПЛ
            'expected_home_xg': 1.8,
            'expected_away_xg': 1.2
        },
        {
            'name': 'Arsenal vs Chelsea',
            'home': 'Arsenal',
            'away': 'Chelsea',
            'league_id': 2,
            'date': datetime(2024, 4, 23),  # Реальный матч АПЛ
            'expected_home_xg': 1.5,
            'expected_away_xg': 1.1
        },
        {
            'name': 'Real Madrid vs Barcelona',
            'home': 'Real Madrid',
            'away': 'Barcelona',
            'league_id': 4,
            'date': datetime(2024, 4, 21),  # Эль Класико
            'expected_home_xg': 1.6,
            'expected_away_xg': 1.4
        },
        {
            'name': 'Bayern Munich vs Dortmund',
            'home': 'Bayern Munich',
            'away': 'Borussia Dortmund',
            'league_id': 5,
            'date': datetime(2024, 3, 30),  # Der Klassiker
            'expected_home_xg': 2.0,
            'expected_away_xg': 1.0
        },
        {
            'name': 'PSG vs Marseille',
            'home': 'Paris Saint Germain',
            'away': 'Marseille',
            'league_id': 7,
            'date': datetime(2024, 3, 31),  # Le Classique
            'expected_home_xg': 2.2,
            'expected_away_xg': 0.8
        },
        {
            'name': 'Inter vs Juventus',
            'home': 'Inter',
            'away': 'Juventus',
            'league_id': 6,
            'date': datetime(2024, 2, 4),  # Derby d'Italia
            'expected_home_xg': 1.4,
            'expected_away_xg': 1.2
        }
    ]
    
    results = {'found': 0, 'not_found': 0, 'total_xg': 0}
    
    for i, test in enumerate(test_matches, 1):
        print(f"\n📊 Тест {i}: {test['name']}")
        print(f"   Дата: {test['date'].strftime('%Y-%m-%d')}")
        
        xg_data = await xg_manager.get_xg(
            match_id=i,
            home_team=test['home'],
            away_team=test['away'],
            league_id=test['league_id'],
            match_date=test['date']
        )
        
        if xg_data:
            results['found'] += 1
            results['total_xg'] += xg_data.total_xg
            print(f"   ✅ xG получен!")
            print(f"   • xG дома: {xg_data.home_xg}")
            print(f"   • xG в гостях: {xg_data.away_xg}")
            print(f"   • Всего xG: {xg_data.total_xg}")
            print(f"   • Ожидалось: {test['expected_home_xg']}-{test['expected_away_xg']}")
            print(f"   • Отклонение: {abs(xg_data.home_xg - test['expected_home_xg']):.2f}, {abs(xg_data.away_xg - test['expected_away_xg']):.2f}")
        else:
            results['not_found'] += 1
            print(f"   ❌ xG не найден")
        
        stats = xg_manager.get_stats()
        print(f"   • Осталось запросов: {stats.get('rate_limit_remaining', 'N/A')}")
        
        # Пауза между запросами
        await asyncio.sleep(6)
    
    # Итоговая статистика
    final_stats = xg_manager.get_stats()
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   • Всего запросов: {final_stats['total_requests']}")
    print(f"   • Найдено матчей: {results['found']}")
    print(f"   • Не найдено: {results['not_found']}")
    print(f"   • Успешность поиска: {results['found']/len(test_matches)*100:.1f}%")
    print(f"   • Средний xG: {results['total_xg']/max(1, results['found']):.2f}")
    print(f"   • Осталось запросов в минуту: {final_stats.get('rate_limit_remaining', 'N/A')}")
    
    await xg_manager.close()

async def test_specific_match(match_id: int):
    """Тестирует конкретный матч по ID из football-data.org"""
    
    print(f"\n🔍 Тестирование матча с ID {match_id}...")
    print("-" * 60)
    
    xg_manager = XGManager(config.FOOTBALL_DATA_API_KEY)
    
    xg_data = await xg_manager.get_xg(
        match_id=999,
        football_data_id=match_id
    )
    
    if xg_data:
        print(f"   ✅ xG получен!")
        print(f"   • xG дома: {xg_data.home_xg}")
        print(f"   • xG в гостях: {xg_data.away_xg}")
        print(f"   • Всего xG: {xg_data.total_xg}")
    else:
        print(f"   ❌ xG не найден")
    
    await xg_manager.close()

async def main():
    print("🚀 Тестирование xG провайдера football-data.org")
    print("=" * 70)
    
    # Основной тест
    await test_football_data_xg()
    
    # Тест конкретного матча (найденные ID)
    print("\n" + "=" * 70)
    print("🔍 Тестирование конкретных матчей:")
    await test_specific_match(436219)  # Manchester City vs Liverpool
    await test_specific_match(442946)  # PSG vs Marseille
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main())