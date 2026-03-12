# test_match_details.py
import asyncio
import logging
from api_client import SStatsClient
import config

logging.basicConfig(level=logging.INFO)

async def test_match_details():
    """Тестирует получение деталей конкретного матча"""
    
    client = SStatsClient(
        api_key=config.SSTATS_API_KEY,
        use_mock=False
    )
    
    print("🔍 Получаем LIVE матчи...")
    live_matches = await client.get_live_matches()
    
    if not live_matches:
        print("❌ Нет LIVE матчей")
        return
    
    # Берем первый матч
    match = live_matches[0]
    print(f"\n📊 Анализ матча: {match.home_team.name} vs {match.away_team.name}")
    print(f"🏷️ ID: {match.id}")
    print(f"⚽ Счет: {match.home_score}:{match.away_score}")
    print(f"⏱️ Минута: {match.minute}")
    print(f"🏆 Лига: {match.league_name}")
    
    # Получаем статистику
    print("\n📈 Получение статистики...")
    stats = await client.get_match_statistics(match.id)
    if stats:
        print("✅ Статистика получена")
        # Покажем основные показатели
        if 'shotsOnGoal' in stats:
            print(f"   Удары в створ: {stats.get('shotsOnGoalHome', 0)}:{stats.get('shotsOnGoalAway', 0)}")
        if 'possession' in stats:
            print(f"   Владение: {stats.get('possessionHome', 50)}%:{stats.get('possessionAway', 50)}%")
    else:
        print("❌ Статистика не найдена")
    
    # Получаем события
    print("\n📋 Получение событий...")
    events = await client.get_match_events(match.id)
    print(f"✅ Найдено событий: {len(events)}")
    
    if events:
        print("\nПоследние события:")
        for event in events[-5:]:  # Покажем последние 5
            minute = event.get('elapsed', '?')
            event_type = event.get('name', 'Событие')
            player = event.get('player', {}).get('name', '')
            print(f"   {minute}' - {event_type} {player}")

if __name__ == "__main__":
    asyncio.run(test_match_details())