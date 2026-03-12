# api_client.py
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from models import Match, Team, LiveStats

logger = logging.getLogger(__name__)

class RealSStatsClient:
    """Клиент для работы с реальным SStats API"""
    
    BASE_URL = "https://api.sstats.net"
    
    def __init__(self, api_key: str, timezone: int = 3):
        self.api_key = api_key
        self.timezone = timezone
        
        # Статусы матчей
        self.live_statuses = [3, 4, 5, 6, 7, 11, 18, 19]
        self.finished_statuses = [8, 9, 10, 17]
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Выполняет запрос к API с увеличенным таймаутом"""
        url = f"{self.BASE_URL}{endpoint}"
        request_params = {"apikey": self.api_key}
        if params:
            request_params.update(params)
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "FootballPredictor/1.0"
        }
        
        timeout = aiohttp.ClientTimeout(total=60)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.debug(f"Запрос к API: {url}")
                async with session.get(url, headers=headers, params=request_params) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка API {response.status} для {url}")
                        return None
                    
                    try:
                        data = await response.json()
                        return data
                    except Exception as e:
                        logger.error(f"Не удалось распарсить JSON: {e}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"Таймаут запроса к {url} (60 секунд)")
            return None
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            return None
    
    async def get_live_matches(self) -> List[Match]:
        """Получает LIVE матчи"""
        params = {"Live": "true", "Limit": 50, "TimeZone": self.timezone}
        data = await self._make_request("/Games/list", params)
        return self._parse_matches_list(data)
    
    async def get_today_matches(self) -> List[Match]:
        """Получает матчи на сегодня"""
        params = {"Today": "true", "Limit": 100, "TimeZone": self.timezone}
        data = await self._make_request("/Games/list", params)
        return self._parse_matches_list(data)
    
    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Получает детальную информацию о матче"""
        return await self._make_request(f"/Games/{match_id}")
    
    async def get_match_statistics(self, match_id: int) -> Optional[LiveStats]:
        """Получает статистику матча и преобразует в LiveStats"""
        details = await self.get_match_details(match_id)
        if not details:
            return None
        
        try:
            data = details.get('data', {})
            game = data.get('game', {})
            stats = data.get('statistics', {})
            
            if not stats:
                return None
            
            minute = game.get('elapsed') or 0
            
            # Получаем данные о командах для country_code
            home_team_data = game.get('homeTeam', {})
            away_team_data = game.get('awayTeam', {})
            
            # Парсим country_code
            home_country = None
            away_country = None
            
            if 'country' in home_team_data and isinstance(home_team_data['country'], dict):
                home_country = home_team_data['country'].get('code') or home_team_data['country'].get('name')
            
            if 'country' in away_team_data and isinstance(away_team_data['country'], dict):
                away_country = away_team_data['country'].get('code') or away_team_data['country'].get('name')
            
            live_stats = LiveStats(
                minute=minute,
                shots_home=stats.get('totalShotsHome', 0) or 0,
                shots_away=stats.get('totalShotsAway', 0) or 0,
                shots_ontarget_home=stats.get('shotsOnGoalHome', 0) or 0,
                shots_ontarget_away=stats.get('shotsOnGoalAway', 0) or 0,
                possession_home=float(stats.get('ballPossessionHome', 50) or 50),
                possession_away=100 - float(stats.get('ballPossessionHome', 50) or 50),
                corners_home=stats.get('cornerKicksHome', 0) or 0,
                corners_away=stats.get('cornerKicksAway', 0) or 0,
                fouls_home=stats.get('foulsHome', 0) or 0,
                fouls_away=stats.get('foulsAway', 0) or 0,
                yellow_cards_home=stats.get('yellowCardsHome', 0) or 0,
                yellow_cards_away=stats.get('yellowCardsAway', 0) or 0,
                dangerous_attacks_home=stats.get('dangerousAttacksHome', 0) or 0,
                dangerous_attacks_away=stats.get('dangerousAttacksAway', 0) or 0
            )
            
            logger.info(f"Статистика матча {match_id}: {live_stats.total_shots} ударов, {live_stats.total_shots_ontarget} в створ")
            return live_stats
            
        except Exception as e:
            logger.error(f"Ошибка парсинга статистики: {e}")
            return None
    
    async def get_match_events(self, match_id: int) -> List[Dict]:
        """Получает события матча"""
        details = await self.get_match_details(match_id)
        if details:
            data = details.get('data', {})
            events = data.get('events', [])
            if events:
                logger.debug(f"Получено {len(events)} событий для матча {match_id}")
            return events
        return []
    
    def _parse_matches_list(self, data: Optional[Dict]) -> List[Match]:
        """Парсит список матчей"""
        matches = []
        
        if not data or not isinstance(data, dict):
            return matches
        
        games_data = data.get('data', [])
        if not isinstance(games_data, list):
            return matches
        
        for item in games_data:
            try:
                match = self._parse_game_item(item)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.error(f"Ошибка парсинга матча: {e}")
        
        logger.info(f"Получено матчей: {len(matches)}")
        return matches
    
    def _parse_game_item(self, item: Dict) -> Optional[Match]:
        """Парсит один матч"""
        if not isinstance(item, dict):
            return None
        
        match_id = item.get('id')
        if not match_id:
            return None
        
        # Парсим команды с country_code
        home_team_data = item.get('homeTeam', {})
        away_team_data = item.get('awayTeam', {})
        
        # Получаем страну из данных команды
        home_country = None
        away_country = None
        
        if 'country' in home_team_data and isinstance(home_team_data['country'], dict):
            home_country = home_team_data['country'].get('code') or home_team_data['country'].get('name')
        
        if 'country' in away_team_data and isinstance(away_team_data['country'], dict):
            away_country = away_team_data['country'].get('code') or away_team_data['country'].get('name')
        
        home_team = Team(
            id=home_team_data.get('id', 0),
            name=home_team_data.get('name', 'Unknown'),
            country_code=home_country,
            logo_url=home_team_data.get('logoUrl')
        )
        away_team = Team(
            id=away_team_data.get('id', 0),
            name=away_team_data.get('name', 'Unknown'),
            country_code=away_country,
            logo_url=away_team_data.get('logoUrl')
        )
        
        # Статус
        status = item.get('status', 0)
        status_name = item.get('statusName')
        
        # Счет
        home_score = item.get('homeResult') or item.get('homeFTResult') or 0
        away_score = item.get('awayResult') or item.get('awayFTResult') or 0
        
        # Минута
        elapsed = item.get('elapsed')
        
        # Лига
        season = item.get('season', {})
        league = season.get('league', {})
        league_name = league.get('name')
        league_id = league.get('id')
        
        # Время начала
        start_time = None
        date_str = item.get('date')
        if date_str:
            try:
                start_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        return Match(
            id=match_id,
            home_team=home_team,
            away_team=away_team,
            status=status,
            status_name=status_name,
            minute=elapsed,
            home_score=home_score,
            away_score=away_score,
            league_id=league_id,
            league_name=league_name,
            start_time=start_time
        )


class SStatsClient:
    """Клиент с поддержкой демо-режима"""
    
    def __init__(self, api_key: str, timezone: int = 3, use_mock: bool = False):
        self.use_mock = use_mock
        self.timezone = timezone
        self.api_key = api_key
        self.real_client = RealSStatsClient(api_key, timezone) if not use_mock else None
        
        if use_mock:
            logger.info("🔄 Используется ДЕМО-режим")
        else:
            logger.info("🌐 Используется реальный API")
    
    async def get_live_matches(self) -> List[Match]:
        if self.use_mock:
            return self._get_mock_matches()
        return await self.real_client.get_live_matches()
    
    async def get_today_matches(self) -> List[Match]:
        if self.use_mock:
            return self._get_mock_matches()
        return await self.real_client.get_today_matches()
    
    async def get_match_statistics(self, match_id: int):
        if self.use_mock:
            return self._get_mock_stats()
        return await self.real_client.get_match_statistics(match_id)
    
    async def get_match_events(self, match_id: int) -> List[Dict]:
        if self.use_mock:
            return []
        return await self.real_client.get_match_events(match_id)
    
    def _get_mock_matches(self) -> List[Match]:
        """Создает тестовые матчи для демо-режима"""
        from datetime import datetime, timedelta
        matches = []
        
        teams = [
            ("Манчестер Сити", "Ливерпуль", "england", "england"),
            ("Реал Мадрид", "Барселона", "spain", "spain"),
            ("Бавария", "Боруссия Д", "germany", "germany"),
            ("ПСЖ", "Марсель", "france", "france"),
            ("Ювентус", "Милан", "italy", "italy")
        ]
        
        for i, (home, away, home_country, away_country) in enumerate(teams):
            match = Match(
                id=1000 + i,
                home_team=Team(id=i*2, name=home, country_code=home_country),
                away_team=Team(id=i*2+1, name=away, country_code=away_country),
                status=3,
                status_name="First Half",
                minute=30 + i*5,
                home_score=i % 2,
                away_score=(i+1) % 2,
                league_name="Тестовая лига",
                start_time=datetime.now() - timedelta(minutes=30)
            )
            matches.append(match)
        
        return matches
    
    def _get_mock_stats(self):
        """Создает тестовую статистику"""
        import random
        return LiveStats(
            minute=45,
            shots_home=random.randint(5, 12),
            shots_away=random.randint(3, 10),
            shots_ontarget_home=random.randint(2, 6),
            shots_ontarget_away=random.randint(1, 4),
            possession_home=random.randint(45, 65),
            possession_away=random.randint(35, 55),
            corners_home=random.randint(2, 6),
            corners_away=random.randint(1, 5),
            fouls_home=random.randint(5, 10),
            fouls_away=random.randint(5, 10)
        )