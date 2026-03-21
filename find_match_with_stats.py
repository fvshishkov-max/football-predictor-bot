# find_match_with_stats.py
"""
Поиск матча с реальной статистикой
"""

import asyncio
from api_client import UnifiedFastClient

async def find_match_with_stats():
    print("="*60)
    print("ПОИСК МАТЧА С РЕАЛЬНОЙ СТАТИСТИКОЙ")
    print("="*60)
    
    client = UnifiedFastClient()
    
    # Получаем live матчи
    matches = await client.get_live_matches()
    print(f"\nНайдено live матчей: {len(matches)}")
    
    found = False
    
    for match in matches:
        # Получаем статистику
        stats = await client.get_match_statistics(match)
        
        if stats:
            home = match.home_team.name if match.home_team else "?"
            away = match.away_team.name if match.away_team else "?"
            minute = match.minute or 0
            score = f"{match.home_score or 0}:{match.away_score or 0}"
            
            xg_home = stats.get('xg_home', 0.5)
            xg_away = stats.get('xg_away', 0.5)
            shots_home = stats.get('shots_home', 0)
            shots_away = stats.get('shots_away', 0)
            shots_ontarget_home = stats.get('shots_ontarget_home', 0)
            shots_ontarget_away = stats.get('shots_ontarget_away', 0)
            possession_home = stats.get('possession_home', 50)
            possession_away = stats.get('possession_away', 50)
            corners_home = stats.get('corners_home', 0)
            corners_away = stats.get('corners_away', 0)
            
            has_stats = (shots_home > 0 or shots_away > 0 or 
                        shots_ontarget_home > 0 or shots_ontarget_away > 0 or
                        xg_home != 0.5 or xg_away != 0.5 or
                        corners_home > 0 or corners_away > 0)
            
            if has_stats:
                found = True
                print(f"\n✅ НАЙДЕН МАТЧ СО СТАТИСТИКОЙ!")
                print(f"\n📋 {home} vs {away}")
                print(f"   Минута: {minute}', Счет: {score}")
                print(f"\n📊 СТАТИСТИКА:")
                print(f"   Удары: {shots_home} : {shots_away}")
                print(f"   Удары в створ: {shots_ontarget_home} : {shots_ontarget_away}")
                print(f"   xG: {xg_home:.2f} : {xg_away:.2f}")
                print(f"   Владение: {possession_home}% : {possession_away}%")
                print(f"   Угловые: {corners_home} : {corners_away}")
                
                # Сохраняем статистику в match
                match.stats = stats
                print(f"\n✅ Статистика сохранена в match.stats")
                
                # Показываем как будет выглядеть сигнал
                print(f"\n📨 Будет отправлен сигнал со статистикой!")
                break
    
    if not found:
        print("\n❌ Не найден матч со статистикой")
        print("\nВозможные причины:")
        print("  1. Матчи только начались (первые 10-15 минут)")
        print("  2. Статистика не собирается для этих лиг")
        print("  3. Нужно подождать накопления данных")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(find_match_with_stats())