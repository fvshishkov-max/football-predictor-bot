# fix_sstats_parsing.py
"""
Исправление парсинга статистики из SStats API
"""

import re

def fix_sstats_parsing():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправленный метод _parse_statistics для SStats
    new_parse = '''    def _parse_statistics(self, details: Dict) -> Optional[Dict]:
        """Парсит статистику из ответа SStats API"""
        try:
            data = details.get('data', {})
            game = data.get('game', {})
            statistics = data.get('statistics')
            
            if statistics is None:
                return {
                    'shots_home': 0, 'shots_away': 0,
                    'shots_ontarget_home': 0, 'shots_ontarget_away': 0,
                    'possession_home': 50, 'possession_away': 50,
                    'corners_home': 0, 'corners_away': 0,
                    'xg_home': 0.5, 'xg_away': 0.5,
                    'has_real_stats': False
                }
            
            # Парсим из otherStatsHome/otherStatsAway (xG и другие метрики)
            other_stats_home = statistics.get('otherStatsHome', {}) or {}
            other_stats_away = statistics.get('otherStatsAway', {}) or {}
            
            # Получаем xG
            xg_home = 0.5
            xg_away = 0.5
            
            # Пробуем разные названия поля xG
            xg_fields = ['Expected goals (xG)', 'Expected Goals (xG)', 'xG', 'expected_goals']
            for field in xg_fields:
                if field in other_stats_home:
                    try:
                        xg_home = float(other_stats_home[field])
                        break
                    except:
                        pass
            
            for field in xg_fields:
                if field in other_stats_away:
                    try:
                        xg_away = float(other_stats_away[field])
                        break
                    except:
                        pass
            
            # Парсим удары из homeStats/awayStats
            home_stats = statistics.get('homeStats', {}) or {}
            away_stats = statistics.get('awayStats', {}) or {}
            
            shots_home = 0
            shots_away = 0
            shots_on_target_home = 0
            shots_on_target_away = 0
            possession_home = 50
            possession_away = 50
            corners_home = 0
            corners_away = 0
            
            # Пробуем разные названия полей
            shot_fields = ['Total Shots', 'Shots', 'total_shots', 'shots']
            for field in shot_fields:
                if field in home_stats:
                    shots_home = home_stats.get(field, 0) or 0
                    break
            for field in shot_fields:
                if field in away_stats:
                    shots_away = away_stats.get(field, 0) or 0
                    break
            
            # Удары в створ
            sot_fields = ['Shots on Goal', 'Shots on Target', 'shots_on_target', 'shots_ontarget']
            for field in sot_fields:
                if field in home_stats:
                    shots_on_target_home = home_stats.get(field, 0) or 0
                    break
            for field in sot_fields:
                if field in away_stats:
                    shots_on_target_away = away_stats.get(field, 0) or 0
                    break
            
            # Владение
            poss_fields = ['Ball Possession', 'Possession', 'possession']
            for field in poss_fields:
                if field in home_stats:
                    val = home_stats.get(field, 50)
                    if isinstance(val, str):
                        val = int(val.replace('%', ''))
                    possession_home = float(val)
                    break
            for field in poss_fields:
                if field in away_stats:
                    val = away_stats.get(field, 50)
                    if isinstance(val, str):
                        val = int(val.replace('%', ''))
                    possession_away = float(val)
                    break
            
            # Угловые
            corner_fields = ['Corner Kicks', 'Corners', 'corner_kicks']
            for field in corner_fields:
                if field in home_stats:
                    corners_home = home_stats.get(field, 0) or 0
                    break
            for field in corner_fields:
                if field in away_stats:
                    corners_away = away_stats.get(field, 0) or 0
                    break
            
            result = {
                'shots_home': shots_home,
                'shots_away': shots_away,
                'shots_ontarget_home': shots_on_target_home,
                'shots_ontarget_away': shots_on_target_away,
                'possession_home': possession_home,
                'possession_away': possession_away,
                'corners_home': corners_home,
                'corners_away': corners_away,
                'xg_home': xg_home,
                'xg_away': xg_away,
                'has_real_stats': shots_home > 0 or shots_away > 0 or xg_home != 0.5 or xg_away != 0.5
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга статистики: {e}")
            return None'''
    
    # Находим и заменяем метод
    pattern = r'def _parse_statistics\(self, details: Dict\) -> Optional\[Dict\]:.*?return None'
    content = re.sub(pattern, new_parse, content, flags=re.DOTALL)
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ SStats парсинг исправлен!")
    print("   • Теперь парсит xG из otherStats")
    print("   • Поддерживает разные названия полей")
    print("   • Сохраняет удары, владение, угловые")

def fix_predictor_stats():
    """Исправляет вывод статистики в predictor.py"""
    
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Улучшаем отображение статистики в сигналах
    new_stats_block = '''        if has_stats:
            home_shots = home_stats.get('shots', 0)
            away_shots = away_stats.get('shots', 0)
            home_shots_ontarget = home_stats.get('shots_on_target', 0)
            away_shots_ontarget = away_stats.get('shots_on_target', 0)
            home_xg = home_stats.get('xg', 0.5)
            away_xg = away_stats.get('xg', 0.5)
            home_possession = home_stats.get('possession', 50)
            away_possession = away_stats.get('possession', 50)
            home_corners = home_stats.get('corners', 0)
            away_corners = away_stats.get('corners', 0)
            
            message_lines.extend([
                "",
                "📊 СТАТИСТИКА:",
                f"  • Удары: {home_shots} : {away_shots}",
                f"  • В створ: {home_shots_ontarget} : {away_shots_ontarget}",
                f"  • xG: {home_xg:.2f} : {away_xg:.2f}",
                f"  • Владение: {home_possession:.0f}% : {away_possession:.0f}%",
                f"  • Угловые: {home_corners} : {away_corners}",
            ])'''
    
    # Заменяем старый блок
    pattern = r'if has_stats:.*?message_lines\.extend\(\[.*?\]\)'
    content = re.sub(pattern, new_stats_block, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ predictor.py обновлен")
    print("   • Добавлены угловые и владение в статистику")

if __name__ == "__main__":
    fix_sstats_parsing()
    fix_predictor_stats()
    print("\n" + "="*60)
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("="*60)
    print("\nТеперь в сигналах будет отображаться:")
    print("  • Удары")
    print("  • Удары в створ")
    print("  • xG (ожидаемые голы)")
    print("  • Владение мячом")
    print("  • Угловые")
    print("\nЗапустите бота: python run_fixed.py")