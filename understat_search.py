# understat_search.py
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
import re
import json
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class UnderstatSearch:
    """Поиск матчей на Understat по названиям команд и дате"""
    
    LEAGUE_URLS = {
        'EPL': 'https://understat.com/league/EPL',
        'La_liga': 'https://understat.com/league/La_liga',
        'Bundesliga': 'https://understat.com/league/Bundesliga',
        'Serie_A': 'https://understat.com/league/Serie_A',
        'Ligue_1': 'https://understat.com/league/Ligue_1',
        'RFPL': 'https://understat.com/league/RFPL',
    }
    
    # Альтернативные названия команд (SStats -> Understat)
    TEAM_NAME_MAPPING = {
        'Manchester City': 'Manchester City',
        'Man City': 'Manchester City',
        'Manchester United': 'Manchester United',
        'Man United': 'Manchester United',
        'Liverpool': 'Liverpool',
        'Chelsea': 'Chelsea',
        'Arsenal': 'Arsenal',
        'Tottenham': 'Tottenham',
        'Real Madrid': 'Real Madrid',
        'Barcelona': 'Barcelona',
        'Atletico Madrid': 'Atletico Madrid',
        'Bayern Munich': 'Bayern Munich',
        'Bayern': 'Bayern Munich',
        'Borussia Dortmund': 'Borussia Dortmund',
        'Dortmund': 'Borussia Dortmund',
        'Paris Saint Germain': 'Paris Saint Germain',
        'PSG': 'Paris Saint Germain',
        'Juventus': 'Juventus',
        'Milan': 'Milan',
        'Inter': 'Inter',
        'Roma': 'Roma',
        'Zenit': 'Zenit',
        'Spartak': 'Spartak Moscow',
        'CSKA': 'CSKA Moscow',
        'Lokomotiv': 'Lokomotiv Moscow',
        'Krasnodar': 'Krasnodar',
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}  # Простой кэш для результатов поиска
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def normalize_team_name(self, name: str) -> str:
        """Нормализует название команды для поиска"""
        # Проверяем маппинг
        if name in self.TEAM_NAME_MAPPING:
            return self.TEAM_NAME_MAPPING[name]
        
        # Убираем лишние слова
        name = name.replace('FC', '').replace('United', 'Utd').strip()
        return name
    
    async def find_match(self, home_team: str, away_team: str, 
                        league: str, match_date: datetime) -> Optional[int]:
        """
        Ищет матч на Understat и возвращает его ID
        
        Args:
            home_team: Название домашней команды
            away_team: Название гостевой команды
            league: Название лиги (EPL, La_liga, etc.)
            match_date: Дата матча
            
        Returns:
            ID матча в Understat или None
        """
        cache_key = f"{home_team}_{away_team}_{match_date.date()}"
        if cache_key in self.cache:
            logger.debug(f"Результат поиска получен из кэша: {cache_key}")
            return self.cache[cache_key]
        
        try:
            session = await self._get_session()
            
            # Получаем страницу лиги
            if league not in self.LEAGUE_URLS:
                logger.warning(f"Лига {league} не поддерживается Understat")
                return None
            
            url = self.LEAGUE_URLS[league]
            logger.info(f"Поиск матча {home_team}-{away_team} в {league}")
            
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"Не удалось получить страницу лиги: {response.status}")
                    return None
                
                html = await response.text()
            
            # Парсим список матчей
            match_id = await self._parse_matches(html, home_team, away_team, match_date)
            
            # Сохраняем в кэш
            self.cache[cache_key] = match_id
            
            if match_id:
                logger.info(f"✅ Найден матч {home_team}-{away_team}: ID {match_id}")
            else:
                logger.debug(f"❌ Матч {home_team}-{away_team} не найден")
            
            return match_id
            
        except Exception as e:
            logger.error(f"Ошибка поиска матча: {e}")
            return None
    
    async def _parse_matches(self, html: str, home_team: str, 
                            away_team: str, match_date: datetime) -> Optional[int]:
        """Парсит список матчей из HTML страницы лиги"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем скрипт с данными матчей
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                
                if 'datesData' in script.string:
                    # Извлекаем JSON
                    match = re.search(r'var datesData\s*=\s*(\[.+?\]);', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            
                            # Ищем матч по дате и командам
                            target_date = match_date.strftime('%Y-%m-%d')
                            
                            for day_data in data:
                                if day_data.get('date') == target_date:
                                    for match_data in day_data.get('games', []):
                                        # Нормализуем названия команд для сравнения
                                        match_home = self.normalize_team_name(match_data.get('h', ''))
                                        match_away = self.normalize_team_name(match_data.get('a', ''))
                                        search_home = self.normalize_team_name(home_team)
                                        search_away = self.normalize_team_name(away_team)
                                        
                                        # Проверяем совпадение
                                        if (match_home.lower() in search_home.lower() or 
                                            search_home.lower() in match_home.lower()) and \
                                           (match_away.lower() in search_away.lower() or 
                                            search_away.lower() in match_away.lower()):
                                            return match_data.get('id')
                                        
                                        # Проверяем обратный вариант (на случай перестановки)
                                        if (match_home.lower() in search_away.lower() or 
                                            search_away.lower() in match_home.lower()) and \
                                           (match_away.lower() in search_home.lower() or 
                                            search_home.lower() in match_away.lower()):
                                            return match_data.get('id')
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга JSON: {e}")
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка парсинга матчей: {e}")
            return None
            
            async def find_match_and_get_xg(self, home_team: str, away_team: str,
                                   league: str, match_date: datetime) -> Optional[int]:
        """Находит ID матча и сразу возвращает его"""
        return await self.find_match(home_team, away_team, league, match_date)