# test_match_analysis.py
import asyncio
import logging
from api_client import SStatsClient
import config

logging.basicConfig(level=logging.INFO)

async def get_all_match_data(match_id: int, home_team_id: int, away_team_id: int, league_id: int, year: int):
    """Получает все данные для анализа матча"""
    
    client = SStatsClient(config.SSTATS_API_KEY, use_mock=False)
    
    print(f"\n🔍 Анализ матча {match_id}")
    print("="*50)
    
    # 1. Основная информация о матче
    print("\n1. Детали матча:")
    details = await client.get_match_details(match_id)
    if details:
        game_data = details.get('data', {}).get('game', {})
        print(f"   Статус: {game_data.get('statusName')}")
        print(f"   Счет: {game_data.get('homeResult')}:{game_data.get('awayResult')}")
        print(f"   Минута: {game_data.get('elapsed')}")
    
    # 2. Статистика команд за последние 10 матчей
    print("\n2. История команд:")
    
    # Хозяева
    print(f"\n   🏠 {home_team_id} (хозяева) - последние матчи:")
    home_history = await client.real_client._make_request(
        "/Games/list", 
        {"team": home_team_id, "ended": "true", "limit": 10}
    )
    if home_history and 'data' in home_history:
        home_games = home_history['data']
        wins = sum(1 for g in home_games if g.get('homeResult', 0) > g.get('awayResult', 0) and g.get('homeTeam', {}).get('id') == home_team_id)
        print(f"   Побед: {wins}/10")
    
    # Гости
    print(f"\n   🚀 {away_team_id} (гости) - последние матчи:")
    away_history = await client.real_client._make_request(
        "/Games/list", 
        {"team": away_team_id, "ended": "true", "limit": 10}
    )
    if away_history and 'data' in away_history:
        away_games = away_history['data']
        wins = sum(1 for g in away_games if g.get('awayResult', 0) > g.get('homeResult', 0) and g.get('awayTeam', {}).get('id') == away_team_id)
        print(f"   Побед: {wins}/10")
    
    # 3. Личные встречи
    print("\n3. Личные встречи (H2H):")
    h2h = await client.real_client._make_request(
        "/Games/list", 
        {"bothTeams": f"{home_team_id},{away_team_id}", "ended": "true", "limit": 5}
    )
    if h2h and 'data' in h2h:
        h2h_games = h2h['data']
        print(f"   Всего встреч: {len(h2h_games)}")
        for game in h2h_games[:3]:
            print(f"   • {game.get('homeTeam', {}).get('name')} {game.get('homeResult')}:{game.get('awayResult')} {game.get('awayTeam', {}).get('name')}")
    
    # 4. Рейтинг Glicko
    print("\n4. Рейтинг Glicko 2:")
    glicko = await client.get_glicko_rating(match_id)
    if glicko and 'data' in glicko:
        glicko_data = glicko['data'].get('glicko', {})
        print(f"   Хозяева: {glicko_data.get('homeRating'):.2f} (RD: {glicko_data.get('homeRd'):.2f})")
        print(f"   Гости: {glicko_data.get('awayRating'):.2f} (RD: {glicko_data.get('awayRd'):.2f})")
        print(f"   Вероятность победы хозяев: {glicko_data.get('homeWinProbability', 0)*100:.1f}%")
    
    # 5. Турнирная таблица
    print("\n5. Турнирная таблица:")
    table = await client.real_client._make_request(
        "/Games/season-table", 
        {"league": league_id, "year": year}
    )
    if table and 'data' in table:
        print(f"   Данные таблицы получены")
    
    # 6. Калькуляция прибыли
    print("\n6. Калькуляция прибыли:")
    profits = await client.real_client._make_request("/Games/profits", {"gameId": match_id})
    if profits:
        print(f"   Данные по прибыли получены")
    
    # 7. Текстовая сводка
    print("\n7. Текстовая сводка:")
    summary = await client.real_client._make_request("/Games/text-summary", {"id": match_id})
    if summary:
        print(f"   Сводка получена")
        if 'data' in summary:
            print(f"   {summary['data'][:200]}...")

async def main():
    # Данные из вашего теста
    match_id = 1433966
    home_team_id = 22173  # Fleetwood Town U21
    away_team_id = 20096  # Sheffield Wednesday U21
    league_id = 703  # Professional Development League
    year = 2025
    
    await get_all_match_data(match_id, home_team_id, away_team_id, league_id, year)

if __name__ == "__main__":
    asyncio.run(main())