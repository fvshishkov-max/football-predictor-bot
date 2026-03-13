# test_xg.py (обновленная версия)
import asyncio
import logging
from datetime import datetime, timedelta
from xg_provider import XGManager
from models import Team, Match, LiveStats
from real_understat_ids import UNDERSTAT_MATCHES, find_match_by_teams

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_xg_with_real_ids():
    """Тестирует xG с реальными ID"""
    
    print("🔍 Тестирование xG с реальными ID матчей...")
    print("-" * 50)
    
    xg_manager = XGManager()
    
    # Берем первые 3 матча из нашего списка
    test_ids = list(UNDERSTAT_MATCHES.keys())[:3]
    
    for i, match_id in enumerate(test_ids, 1):
        match_data = UNDERSTAT_MATCHES[match_id]
        print(f"\n📊 Тест {i}: ID {match_id}")
        print(f"   {match_data['home']} vs {match_data['away']}")
        print(f"   Лига: {match_data['league']}")
        print(f"   Дата: {match_data['date']}")
        
        # Пробуем получить xG
        xg_data = await xg_manager.get_xg(
            match_id=i,
            understat_id=match_id,
            home_team=match_data['home'],
            away_team=match_data['away'],
            league=match_data['league'],
            match_date=datetime.strptime(match_data['date'], '%Y-%m-%d')
        )
        
        if xg_data:
            print(f"   ✅ xG получен!")
            print(f"   • xG дома: {xg_data.home_xg:.2f}")
            print(f"   • xG в гостях: {xg_data.away_xg:.2f}")
            print(f"   • Всего xG: {xg_data.total_xg:.2f}")
        else:
            print(f"   ❌ xG не найден")
    
    stats = xg_manager.get_stats()
    print("\n📈 Статистика:", stats)
    await xg_manager.close()

async def test_live_match_with_xg():
    """Тестирует live матч с xG"""
    
    print("\n📡 Тестирование live матча с xG...")
    print("-" * 50)
    
    from predictor import Predictor
    
    # Берем первый матч из списка
    match_id = list(UNDERSTAT_MATCHES.keys())[0]
    match_data = UNDERSTAT_MATCHES[match_id]
    
    # Создаем тестовый матч
    match = Match(
        id=99999,
        home_team=Team(id=1, name=match_data['home'], country_code="eng"),
        away_team=Team(id=2, name=match_data['away'], country_code="eng"),
        league_id=2,
        league_name="Premier League",
        start_time=datetime.now(),
        understat_id=match_id
    )
    
    stats = LiveStats(
        minute=35,
        shots_home=8,
        shots_away=5,
        shots_ontarget_home=4,
        shots_ontarget_away=2,
        possession_home=55,
        possession_away=45
    )
    
    predictor = Predictor()
    analysis = await predictor.analyze_live_match(match, stats)
    
    print(f"\n📊 Анализ матча:")
    print(f"   • Активность: {analysis.activity_level}")
    print(f"   • Потенциал: {analysis.attack_potential}")
    
    if analysis.xg_data:
        print(f"   • xG: {analysis.xg_data.home_xg:.2f}-{analysis.xg_data.away_xg:.2f}")
    
    print("\n📱 Telegram сообщение:")
    print(analysis.format_telegram_message(match))
    
    await predictor.close()

async def main():
    print("🚀 Тестирование xG интеграции")
    print("=" * 60)
    
    await test_xg_with_real_ids()
    await test_live_match_with_xg()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main())