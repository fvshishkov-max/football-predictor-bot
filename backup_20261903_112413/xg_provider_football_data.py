# xg_provider_football_data.py
import aiohttp
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from cachetools import TTLCache
from models import XGData

logger = logging.getLogger(__name__)

class FootballDataXGProvider:
    """Провайдер xG данных через football-data.org API"""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    # Маппинг лиг SStats -> football-data.org competition codes
    LEAGUE_MAPPING = {
        2: 'PL',      # Premier League
        3: 'ELC',     # Championship
        4: 'PD',      # La Liga
        5: 'BL1',     # Bundesliga
        6: 'SA',      # Serie A
        7: 'FL1',     # Ligue 1
        8: 'RSL',     # Russian Premier League
        13: 'PL',     # Premier League
        19: 'SA',     # Serie A
        20: 'BL1',    # Bundesliga
        21: 'PD',     # La Liga
        22: 'FL1',    # Ligue 1
        201: 'CL',    # Champions League
        202: 'EL',    # Europa League
    }
    
    # Альтернативные названия команд
    TEAM_ALIASES = {
        'Manchester City': ['Man City', 'Manchester City FC', 'MCI'],
        'Manchester United': ['Man United', 'Manchester Utd', 'MUN'],
        'Liverpool': ['Liverpool FC', 'LIV'],
        'Chelsea': ['Chelsea FC', 'CHE'],
        'Arsenal': ['Arsenal FC', 'ARS'],
        'Tottenham': ['Tottenham Hotspur', 'Spurs', 'TOT'],
        'Real Madrid': ['Real Madrid CF', 'RMA'],
        'Barcelona': ['FC Barcelona', 'BAR'],
        'Atletico Madrid': ['Atlético Madrid', 'ATM'],
        'Bayern Munich': ['FC Bayern München', 'Bayern München', 'BAY'],
        'Borussia Dortmund': ['BVB', 'Dortmund', 'BOR'],
        'Paris Saint Germain': ['PSG', 'Paris SG', 'PAR'],
        'Juventus': ['Juventus FC', 'JUV'],
        'Milan': ['AC Milan', 'ACM'],
        'Inter': ['Inter Milan', 'Internazionale', 'INT'],
        'Roma': ['AS Roma', 'ROM'],
        'Napoli': ['SSC Napoli', 'NAP'],
    }
    
    def __init__(self, api_key: str, cache_ttl: int = 3600):
        self.api_key = api_key
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_delay = 6  # 10 requests per minute
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0,
            'rate_limit_remaining': None,
            'rate_limit_reset': None
        }
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'X-Auth-Token': self.api_key,
                    'User-Agent': 'Football Predictor Bot/1.0'
                }
            )
        return self.session
    
    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _wait_for_rate_limit(self):
        """Соблюдает rate limiting"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            logger.debug(f"Ожидание {wait_time:.1f}с")
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _update_rate_limit(self, headers):
        """Обновляет информацию о rate limit"""
        remaining = headers.get('X-Requests-Available-Minute')
        reset = headers.get('X-RequestCounter-Reset')
        
        if remaining:
            self.stats['rate_limit_remaining'] = int(remaining)
        if reset:
            self.stats['rate_limit_reset'] = int(reset)
    
    def _normalize_team_name(self, name: str) -> List[str]:
        """Возвращает все возможные варианты названия команды"""
        name_lower = name.lower().strip()
        variants = [name_lower]
        
        # Добавляем алиасы
        for key, aliases in self.TEAM_ALIASES.items():
            if key.lower() in name_lower or name_lower in key.lower():
                variants.extend([a.lower() for a in aliases])
                variants.append(key.lower())
        
        # Убираем дубликаты
        return list(set(variants))
    
    def _team_matches(self, team1: str, team2: str) -> bool:
        """Проверяет, соответствуют ли названия команд"""
        variants1 = self._normalize_team_name(team1)
        variants2 = self._normalize_team_name(team2)
        
        for v1 in variants1:
            for v2 in variants2:
                if v1 in v2 or v2 in v1:
                    return True
        return False
    
    def get_league_code(self, league_id: Optional[int]) -> Optional[str]:
        """Получает код лиги для football-data.org"""
        if league_id and league_id in self.LEAGUE_MAPPING:
            return self.LEAGUE_MAPPING[league_id]
        return None
    
    async def get_competition_matches(self, competition_code: str, date_from: str, date_to: str) -> List[Dict]:
        """Получает все матчи лиги за период"""
        cache_key = f"comp_{competition_code}_{date_from}_{date_to}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            await self._wait_for_rate_limit()
            session = await self._get_session()
            
            url = f"{self.BASE_URL}/competitions/{competition_code}/matches"
            params = {
                'dateFrom': date_from,
                'dateTo': date_to,
                'status': 'FINISHED'
            }
            
            async with session.get(url, params=params) as response:
                self._update_rate_limit(response.headers)
                
                if response.status == 200:
                    data = await response.json()
                    matches = data.get('matches', [])
                    self.cache[cache_key] = matches
                    return matches
                else:
                    logger.warning(f"Ошибка {response.status} для {competition_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка получения матчей: {e}")
            return []
    
    async def search_match(self, home_team: str, away_team: str, 
                          competition_code: str, match_date: datetime) -> Optional[Dict]:
        """Улучшенный поиск матча с несколькими попытками"""
        cache_key = f"search_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Пробуем искать за день до и после, если в указанную дату нет матчей
        search_dates = [
            match_date,
            match_date - timedelta(days=1),
            match_date + timedelta(days=1)
        ]
        
        for search_date in search_dates:
            date_from = search_date.strftime('%Y-%m-%d')
            date_to = (search_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            logger.info(f"Поиск в {competition_code} за {date_from}")
            matches = await self.get_competition_matches(competition_code, date_from, date_to)
            
            if matches:
                for match in matches:
                    match_home = match.get('homeTeam', {}).get('name', '')
                    match_away = match.get('awayTeam', {}).get('name', '')
                    
                    if self._team_matches(home_team, match_home) and self._team_matches(away_team, match_away):
                        self.cache[cache_key] = match
                        logger.info(f"✅ Найден матч за {search_date.strftime('%Y-%m-%d')}")
                        return match
                    
                    if self._team_matches(home_team, match_away) and self._team_matches(away_team, match_home):
                        self.cache[cache_key] = match
                        logger.info(f"✅ Найден матч за {search_date.strftime('%Y-%m-%d')} (перестановка)")
                        return match
        
        logger.debug(f"Матч не найден ни в одной из дат")
        self.cache[cache_key] = None
        return None
    
    async def get_match_xg(self, match_id: int, football_data_id: Optional[int] = None,
                          home_team: Optional[str] = None, away_team: Optional[str] = None,
                          competition_code: Optional[str] = None, 
                          match_date: Optional[datetime] = None) -> Optional[XGData]:
        """Получает xG для матча с повторными попытками"""
        self.stats['total_requests'] += 1
        
        cache_key = f"xg_{match_id}"
        if cache_key in self.cache:
            self.stats['cached_requests'] += 1
            logger.debug(f"xG для матча {match_id} получен из кэша")
            return self.cache[cache_key]
        
        # Поиск матча если нет ID
        if not football_data_id and all([home_team, away_team, competition_code, match_date]):
            logger.info(f"Поиск xG для {home_team} vs {away_team} в {competition_code}")
            match_data = await self.search_match(home_team, away_team, competition_code, match_date)
            if match_data:
                football_data_id = match_data.get('id')
                logger.info(f"Найден football_data_id {football_data_id}")
        
        if not football_data_id:
            logger.debug(f"Нет football_data_id для матча {match_id}")
            self.stats['failed_requests'] += 1
            return None
        
        # Повторные попытки запроса
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self._wait_for_rate_limit()
                session = await self._get_session()
                
                url = f"{self.BASE_URL}/matches/{football_data_id}"
                logger.info(f"Запрос матча {football_data_id} (попытка {attempt + 1})")
                
                async with session.get(url) as response:
                    self._update_rate_limit(response.headers)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Получаем счет
                        score = data.get('score', {}).get('fullTime', {})
                        home_goals = score.get('home', 0)
                        away_goals = score.get('away', 0)
                        
                        # Более точная оценка xG
                        home_xg = self._estimate_xg_from_goals(home_goals, away_goals, is_home=True)
                        away_xg = self._estimate_xg_from_goals(away_goals, home_goals, is_home=False)
                        
                        xg_data = XGData(
                            home_xg=round(home_xg, 1),
                            away_xg=round(away_xg, 1),
                            total_xg=round(home_xg + away_xg, 1),
                            source='football-data.org',
                            understat_id=football_data_id
                        )
                        
                        self.stats['successful_requests'] += 1
                        self.cache[cache_key] = xg_data
                        logger.info(f"✅ xG для матча {match_id}: {xg_data.home_xg:.1f}-{xg_data.away_xg:.1f} (голы: {home_goals}-{away_goals})")
                        return xg_data
                        
                    elif response.status == 429:
                        logger.warning(f"Rate limit exceeded, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(10 * (attempt + 1))
                    else:
                        logger.warning(f"Ошибка {response.status} для матча {football_data_id}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(5)
                            
            except Exception as e:
                logger.error(f"Ошибка при попытке {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        self.stats['failed_requests'] += 1
        return None
        
    def _estimate_xg_from_goals(self, team_goals: int, opponent_goals: int, is_home: bool) -> float:
        """Оценивает xG на основе забитых и пропущенных голов"""
        if team_goals == 0 and opponent_goals == 0:
            return 0.3  # Сухая ничья
        
        if team_goals == 0:
            return opponent_goals * 0.2  # Не забили, но пропустили
        
        # Базовый xG от забитых голов
        base_xg = team_goals * 0.8
        
        # Корректировка для крупных счетов
        if team_goals >= 4:
            base_xg = team_goals * 0.6
        elif team_goals >= 3:
            base_xg = team_goals * 0.7
        
        # Бонус за игру дома
        if is_home:
            base_xg *= 1.1
        
        return base_xg
    
    def get_stats(self) -> Dict:
        """Возвращает статистику"""
        total = self.stats['total_requests']
        return {
            'total_requests': total,
            'successful': self.stats['successful_requests'],
            'failed': self.stats['failed_requests'],
            'cached': self.stats['cached_requests'],
            'rate_limit_remaining': self.stats['rate_limit_remaining'],
            'success_rate': round((self.stats['successful_requests'] / max(1, total)) * 100, 1)
        }