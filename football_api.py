# football_api.py
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
import sqlite3
from models import Match, Team, LiveStats
from api_client import SStatsClient

logger = logging.getLogger(__name__)

class FootballDataClient:
    """Клиент для Football-Data.org API"""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Auth-Token": api_key,
            "Accept": "application/json"
        }
        self.last_request_time = 0
        self.min_request_interval = 6  # 10 запросов в минуту максимум
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Выполняет запрос к API с rate limiting"""
        
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            logger.debug(f"⏳ Ожидание {wait_time:.1f}с перед запросом к Football-Data.org")
            await asyncio.sleep(wait_time)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        timeout = aiohttp.ClientTimeout(total=30)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"📡 Запрос к Football-Data.org: {url}")
                    async with session.get(url, headers=self.headers, params=params) as response:
                        
                        self.last_request_time = datetime.now().timestamp()
                        
                        if response.status == 429:
                            retry_after = 60
                            logger.warning(f"⚠️ Rate limit (429), ожидание {retry_after}с")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status == 403:
                            logger.error("❌ Ошибка 403: Неверный API ключ или нет доступа")
                            return None
                        
                        if response.status != 200:
                            logger.error(f"❌ Ошибка API {response.status} для {url}")
                            return None
                        
                        data = await response.json()
                        return data
                        
            except asyncio.TimeoutError:
                logger.error(f"⏰ Таймаут запроса к {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Ошибка запроса: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        return None
    
    async def get_live_matches(self) -> List[Match]:
        """Получает live матчи"""
        params = {"status": "LIVE"}
        data = await self._make_request("/matches", params)
        return self._parse_matches(data)
    
    async def get_today_matches(self) -> List[Match]:
        """Получает матчи на сегодня"""
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"dateFrom": today, "dateTo": today}
        data = await self._make_request("/matches", params)
        return self._parse_matches(data)
    
    async def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Получает детали матча"""
        return await self._make_request(f"/matches/{match_id}")
    
    def _parse_matches(self, data: Optional[Dict]) -> List[Match]:
        """Парсит список матчей"""
        matches = []
        
        if not data or 'matches' not in data:
            return matches
        
        for item in data['matches']:
            try:
                match = self._parse_match(item)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга матча: {e}")
        
        logger.info(f"📊 Получено матчей из Football-Data.org: {len(matches)}")
        return matches
    
    def _parse_match(self, item: Dict) -> Optional[Match]:
        """Парсит один матч"""
        match_id = item.get('id')
        if not match_id:
            return None
        
        # Команды
        home_team_data = item.get('homeTeam', {})
        away_team_data = item.get('awayTeam', {})
        
        home_team = Team(
            id=home_team_data.get('id', 0),
            name=home_team_data.get('name', 'Unknown'),
            country_code=item.get('area', {}).get('code'),
            logo_url=None
        )
        away_team = Team(
            id=away_team_data.get('id', 0),
            name=away_team_data.get('name', 'Unknown'),
            country_code=item.get('area', {}).get('code'),
            logo_url=None
        )
        
        # Счет
        score = item.get('score', {}).get('fullTime', {})
        home_score = score.get('home', 0) or 0
        away_score = score.get('away', 0) or 0
        
        # Статус
        status = item.get('status', '')
        minute = None
        if status == 'LIVE':
            minute = item.get('minute', 0)
        
        # Лига
        competition = item.get('competition', {})
        league_id = competition.get('id')
        league_name = competition.get('name')
        
        # Время начала
        start_time = None
        date_str = item.get('utcDate')
        if date_str:
            try:
                start_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        return Match(
            id=match_id,
            home_team=home_team,
            away_team=away_team,
            status=1 if status == 'LIVE' else 0,
            status_name=status,
            minute=minute,
            home_score=home_score,
            away_score=away_score,
            league_id=league_id,
            league_name=league_name,
            start_time=start_time
        )


class CacheDatabase:
    """Кэширующая база данных SQLite"""
    
    def __init__(self, db_path: str = 'data/football_cache.db'):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Инициализирует базу данных"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица для кэша матчей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS matches_cache (
                        match_id INTEGER PRIMARY KEY,
                        home_team_id INTEGER,
                        away_team_id INTEGER,
                        home_team_name TEXT,
                        away_team_name TEXT,
                        home_score INTEGER,
                        away_score INTEGER,
                        status TEXT,
                        minute INTEGER,
                        league_id INTEGER,
                        league_name TEXT,
                        country_code TEXT,
                        last_updated TEXT,
                        data_json TEXT
                    )
                ''')
                
                # Таблица для статистики
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics_cache (
                        match_id INTEGER,
                        stat_name TEXT,
                        home_value REAL,
                        away_value REAL,
                        last_updated TEXT,
                        PRIMARY KEY (match_id, stat_name)
                    )
                ''')
                
                # Таблица для истории команд
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS team_history (
                        team_id INTEGER,
                        match_id INTEGER,
                        date TEXT,
                        opponent_id INTEGER,
                        home_away TEXT,
                        goals_for INTEGER,
                        goals_against INTEGER,
                        xg_for REAL,
                        xg_against REAL,
                        shots INTEGER,
                        shots_on_target INTEGER,
                        corners INTEGER,
                        possession INTEGER,
                        league_id INTEGER,
                        PRIMARY KEY (team_id, match_id)
                    )
                ''')
                
                conn.commit()
                logger.info(f"✅ Кэш-база данных инициализирована в {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации кэш-БД: {e}")
    
    def save_match(self, match: Match, stats: Optional[Dict] = None):
        """Сохраняет матч в кэш"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Сохраняем основные данные
                cursor.execute('''
                    INSERT OR REPLACE INTO matches_cache
                    (match_id, home_team_id, away_team_id, home_team_name, away_team_name,
                     home_score, away_score, status, minute, league_id, league_name,
                     country_code, last_updated, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match.id,
                    match.home_team.id,
                    match.away_team.id,
                    match.home_team.name,
                    match.away_team.name,
                    match.home_score or 0,
                    match.away_score or 0,
                    match.status_name or 'UNKNOWN',
                    match.minute or 0,
                    match.league_id,
                    match.league_name,
                    match.home_team.country_code,
                    datetime.now().isoformat(),
                    json.dumps(match.__dict__, default=str)
                ))
                
                # Сохраняем статистику
                if stats and isinstance(stats, dict):
                    stat_mappings = [
                        ('shots', stats.get('shots_home', 0), stats.get('shots_away', 0)),
                        ('shots_on_target', stats.get('shots_ontarget_home', 0), stats.get('shots_ontarget_away', 0)),
                        ('possession', stats.get('possession_home', 50), stats.get('possession_away', 50)),
                        ('corners', stats.get('corners_home', 0), stats.get('corners_away', 0)),
                        ('fouls', stats.get('fouls_home', 0), stats.get('fouls_away', 0)),
                        ('yellow_cards', stats.get('yellow_cards_home', 0), stats.get('yellow_cards_away', 0)),
                        ('dangerous_attacks', stats.get('dangerous_attacks_home', 0), stats.get('dangerous_attacks_away', 0)),
                        ('xg', stats.get('xg_home', 0), stats.get('xg_away', 0))
                    ]
                    
                    for stat_name, home_val, away_val in stat_mappings:
                        cursor.execute('''
                            INSERT OR REPLACE INTO statistics_cache
                            (match_id, stat_name, home_value, away_value, last_updated)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (match.id, stat_name, home_val, away_val, datetime.now().isoformat()))
                
                conn.commit()
                logger.debug(f"💾 Матч {match.id} сохранен в кэш")
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш: {e}")
    
    def get_match(self, match_id: int) -> Optional[Dict]:
        """Получает матч из кэша"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM matches_cache WHERE match_id = ?
                ''', (match_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'match_id': row[0],
                        'home_team_id': row[1],
                        'away_team_id': row[2],
                        'home_team_name': row[3],
                        'away_team_name': row[4],
                        'home_score': row[5],
                        'away_score': row[6],
                        'status': row[7],
                        'minute': row[8],
                        'league_id': row[9],
                        'league_name': row[10],
                        'country_code': row[11],
                        'last_updated': row[12]
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка чтения из кэша: {e}")
            return None
    
    def get_statistics(self, match_id: int) -> Dict[str, Dict]:
        """Получает статистику матча из кэша"""
        stats = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT stat_name, home_value, away_value FROM statistics_cache
                    WHERE match_id = ?
                ''', (match_id,))
                
                for row in cursor.fetchall():
                    stat_name, home_val, away_val = row
                    stats[stat_name] = {'home': home_val, 'away': away_val}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка чтения статистики из кэша: {e}")
        
        return stats
    
    def save_team_history(self, team_id: int, match: Match, stats: Optional[Dict] = None):
        """Сохраняет историю команды"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Определяем, где играла команда
                if team_id == match.home_team.id:
                    home_away = 'home'
                    opponent_id = match.away_team.id
                    goals_for = match.home_score or 0
                    goals_against = match.away_score or 0
                    xg_for = stats.get('xg_home', 0) if stats else 0
                    xg_against = stats.get('xg_away', 0) if stats else 0
                    shots = stats.get('shots_home', 0) if stats else 0
                    shots_on_target = stats.get('shots_ontarget_home', 0) if stats else 0
                    corners = stats.get('corners_home', 0) if stats else 0
                    possession = stats.get('possession_home', 50) if stats else 50
                else:
                    home_away = 'away'
                    opponent_id = match.home_team.id
                    goals_for = match.away_score or 0
                    goals_against = match.home_score or 0
                    xg_for = stats.get('xg_away', 0) if stats else 0
                    xg_against = stats.get('xg_home', 0) if stats else 0
                    shots = stats.get('shots_away', 0) if stats else 0
                    shots_on_target = stats.get('shots_ontarget_away', 0) if stats else 0
                    corners = stats.get('corners_away', 0) if stats else 0
                    possession = stats.get('possession_away', 50) if stats else 50
                
                cursor.execute('''
                    INSERT OR REPLACE INTO team_history
                    (team_id, match_id, date, opponent_id, home_away,
                     goals_for, goals_against, xg_for, xg_against,
                     shots, shots_on_target, corners, possession, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    team_id, match.id, match.start_time.isoformat() if match.start_time else datetime.now().isoformat(),
                    opponent_id, home_away,
                    goals_for, goals_against,
                    xg_for, xg_against,
                    shots, shots_on_target, corners, possession,
                    match.league_id
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения истории команды: {e}")
    
    def get_team_form(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Получает последние матчи команды"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM team_history
                    WHERE team_id = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (team_id, limit))
                
                columns = [description[0] for description in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения формы команды: {e}")
            return []


class UnifiedFootballClient:
    """Унифицированный клиент для всех API"""
    
    def __init__(self, football_data_key: str, sstats_key: str, use_mock: bool = False):
        self.football_data = FootballDataClient(football_data_key) if football_data_key and not use_mock else None
        self.sstats = SStatsClient(sstats_key, use_mock=use_mock) if sstats_key else None
        self.cache = CacheDatabase()
        self.use_mock = use_mock
        
    async def get_live_matches(self) -> List[Match]:
        """Получает live матчи из всех доступных источников"""
        matches = []
        
        # Пробуем получить из Football-Data.org
        if self.football_data:
            try:
                fd_matches = await self.football_data.get_live_matches()
                if fd_matches:
                    logger.info(f"✅ Получено {len(fd_matches)} матчей из Football-Data.org")
                    matches.extend(fd_matches)
                    
                    # Сохраняем в кэш
                    for match in fd_matches:
                        self.cache.save_match(match)
            except Exception as e:
                logger.error(f"❌ Ошибка Football-Data.org: {e}")
        
        # Пробуем получить из SStats
        if self.sstats:
            try:
                sstats_matches = await self.sstats.get_live_matches()
                if sstats_matches:
                    logger.info(f"✅ Получено {len(sstats_matches)} матчей из SStats")
                    
                    # Фильтруем дубликаты
                    existing_ids = {m.id for m in matches}
                    for match in sstats_matches:
                        if match.id not in existing_ids:
                            matches.append(match)
                            
                    # Сохраняем в кэш
                    for match in sstats_matches:
                        self.cache.save_match(match)
            except Exception as e:
                logger.error(f"❌ Ошибка SStats: {e}")
        
        return matches
    
    async def get_match_statistics(self, match: Match) -> Optional[Dict]:
        """Получает статистику матча в виде словаря"""
        stats = None
        
        # Сначала проверяем кэш
        cached_stats = self.cache.get_statistics(match.id)
        if cached_stats:
            logger.info(f"📦 Статистика для матча {match.id} загружена из кэша")
            # Преобразуем кэшированные данные в плоский словарь
            stats = {
                'minute': match.minute or 0,
                'shots_home': cached_stats.get('shots', {}).get('home', 0),
                'shots_away': cached_stats.get('shots', {}).get('away', 0),
                'shots_ontarget_home': cached_stats.get('shots_on_target', {}).get('home', 0),
                'shots_ontarget_away': cached_stats.get('shots_on_target', {}).get('away', 0),
                'possession_home': cached_stats.get('possession', {}).get('home', 50),
                'possession_away': cached_stats.get('possession', {}).get('away', 50),
                'corners_home': cached_stats.get('corners', {}).get('home', 0),
                'corners_away': cached_stats.get('corners', {}).get('away', 0),
                'fouls_home': cached_stats.get('fouls', {}).get('home', 0),
                'fouls_away': cached_stats.get('fouls', {}).get('away', 0),
                'yellow_cards_home': cached_stats.get('yellow_cards', {}).get('home', 0),
                'yellow_cards_away': cached_stats.get('yellow_cards', {}).get('away', 0),
                'dangerous_attacks_home': cached_stats.get('dangerous_attacks', {}).get('home', 0),
                'dangerous_attacks_away': cached_stats.get('dangerous_attacks', {}).get('away', 0),
                'xg_home': cached_stats.get('xg', {}).get('home', 0),
                'xg_away': cached_stats.get('xg', {}).get('away', 0)
            }
            return stats
        
        # Если нет в кэше, пробуем получить из SStats
        if self.sstats:
            stats_dict = await self.sstats.get_match_statistics(match.id)
            if stats_dict and isinstance(stats_dict, dict):
                self.cache.save_match(match, stats_dict)
                self.cache.save_team_history(match.home_team.id, match, stats_dict)
                self.cache.save_team_history(match.away_team.id, match, stats_dict)
                return stats_dict
        
        return None