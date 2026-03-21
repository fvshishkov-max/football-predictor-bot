# fix_api_stats.py
"""
Исправление получения статистики в api_client.py
"""

import re

def fix_api_client():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Улучшаем метод get_match_statistics
    new_method = '''    async def get_match_statistics(self, match: Match) -> Optional[Dict]:
        """Получает статистику матча с правильным парсингом"""
        if self.sstats and not self.use_mock:
            stats = await self.sstats.get_match_statistics(match.id)
            if stats:
                return stats
        
        if self.rapidapi and not self.use_mock:
            stats = await self.rapidapi.get_match_statistics(match.id)
            if stats:
                return stats
        
        # Базовый ответ с пустой статистикой
        return {
            'shots_home': 0, 'shots_away': 0,
            'shots_ontarget_home': 0, 'shots_ontarget_away': 0,
            'possession_home': 50, 'possession_away': 50,
            'corners_home': 0, 'corners_away': 0,
            'xg_home': 0.5, 'xg_away': 0.5,
            'has_real_stats': False
        }'''
    
    # Заменяем метод
    pattern = r'async def get_match_statistics\(self, match: Match\) -> Optional\[Dict\]:.*?return \{'
    content = re.sub(pattern, new_method, content, flags=re.DOTALL)
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ api_client.py исправлен")

def fix_optimized_sstats():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Улучшаем парсинг статистики в OptimizedSStatsClient
    new_parse = '''    def _parse_statistics(self, details: Dict) -> Optional[Dict]:
        """Парсит статистику из ответа API"""
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
            
            # Парсим основную статистику
            home_stats = statistics.get('homeStats', {})
            away_stats = statistics.get('awayStats', {})
            other_stats_home = statistics.get('otherStatsHome', {})
            other_stats_away = statistics.get('otherStatsAway', {})
            
            # Получаем xG
            xg_home = 0.5
            xg_away = 0.5
            if 'Expected goals (xG)' in other_stats_home:
                try:
                    xg_home = float(other_stats_home['Expected goals (xG)'])
                except:
                    pass
            if 'Expected goals (xG)' in other_stats_away:
                try:
                    xg_away = float(other_stats_away['Expected goals (xG)'])
                except:
                    pass
            
            result = {
                'shots_home': home_stats.get('Total Shots', 0) or 0,
                'shots_away': away_stats.get('Total Shots', 0) or 0,
                'shots_ontarget_home': home_stats.get('Shots on Goal', 0) or 0,
                'shots_ontarget_away': away_stats.get('Shots on Goal', 0) or 0,
                'possession_home': float(home_stats.get('Ball Possession', 50)) or 50,
                'possession_away': float(away_stats.get('Ball Possession', 50)) or 50,
                'corners_home': home_stats.get('Corner Kicks', 0) or 0,
                'corners_away': away_stats.get('Corner Kicks', 0) or 0,
                'xg_home': xg_home,
                'xg_away': xg_away,
                'has_real_stats': True
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
    
    print("✅ Парсинг статистики исправлен")

if __name__ == "__main__":
    fix_api_client()
    fix_optimized_sstats()
    print("\nПерезапустите бота: python run_fixed.py")