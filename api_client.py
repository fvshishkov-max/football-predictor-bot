# api_client.py
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
import random

from models import Match, Team, LiveStats
import config

logger = logging.getLogger(__name__)

class RapidAPIClient:
    """Клиент для api-football.com через RapidAPI"""
    
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        self.session = None
        self.request_times = []
    
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        url = f"{self.BASE_URL}{endpoint}"
        
        now = datetime.now().timestamp()
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        if len(self.request_times) >= 5:
            wait_time = 1.0 - (now - self.request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        
        try:
            session = await self._get_session()
            async with session.get(url, headers=self.headers, params=params, timeout=timeout) as response:
                self.request_times.append(datetime.now().timestamp())
                
                if response.status != 200:
                    logger.error(f"Ошибка API {response.status} для {url}")
                    return None
                
                return await response.json()
                
        except asyncio.TimeoutError:
            logger.error(f"Таймаут запроса к {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            return None
    
    async def get_live_matches(self) -> List[Match]:
        params = {"live": "all"}
        data = await self._make_request("/fixtures", params)
        return self._parse_matches(data)
    
    async def get_match_statistics(self, fixture_id: int) -> Optional[Dict]:
        params = {"fixture": fixture_id}
        data = await self._make_request("/fixtures/statistics", params)
        return self._parse_statistics(data)
    
    def _parse_matches(self, data: Optional[Dict]) -> List[Match]:
        matches = []
        if not data or 'response' not in data:
            return matches
        
        for item in data['response']:
            try:
                match = self._parse_match(item)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.error(f"Ошибка парсинга матча: {e}")
        
        return matches
    
    def _parse_match(self, item: Dict) -> Optional[Match]:
        fixture = item.get('fixture', {})
        league = item.get('league', {})
        teams = item.get('teams', {})
        goals = item.get('goals', {})
        
        match_id = fixture.get('id')
        if not match_id:
            return None
        
        home_team = Team(
            id=teams.get('home', {}).get('id', 0),
            name=teams.get('home', {}).get('name', 'Unknown'),
            country_code=league.get('country', {}).get('code'),
            logo_url=teams.get('home', {}).get('logo')
        )
        
        away_team = Team(
            id=teams.get('away', {}).get('id', 0),
            name=teams.get('away', {}).get('name', 'Unknown'),
            country_code=league.get('country', {}).get('code'),
            logo_url=teams.get('away', {}).get('logo')
        )
        
        status = fixture.get('status', {}).get('short', '')
        elapsed = fixture.get('status', {}).get('elapsed', 0)
        
        return Match(
            id=match_id,
            home_team=home_team,
            away_team=away_team,
            status=1 if status == 'LIVE' else 0,
            status_name=status,
            minute=elapsed,
            home_score=goals.get('home', 0) or 0,
            away_score=goals.get('away', 0) or 0,
            league_id=league.get('id'),
            league_name=league.get('name'),
            start_time=datetime.fromisoformat(fixture.get('date', '').replace('Z', '+00:00')) if fixture.get('date') else None
        )
    
    def _parse_statistics(self, data: Optional[Dict]) -> Optional[Dict]:
        if not data or 'response' not in data or not data['response']:
            return None
        
        stats_dict = {
            'shots_home': 0, 'shots_away': 0,
            'shots_ontarget_home': 0, 'shots_ontarget_away': 0,
            'possession_home': 50, 'possession_away': 50,
            'corners_home': 0, 'corners_away': 0,
            'xg_home': 0.5, 'xg_away': 0.5,
            'has_real_stats': False
        }
        
        for team_stats in data['response']:
            team = team_stats.get('team', {}).get('name', '')
            statistics = team_stats.get('statistics', [])
            
            is_home = 'home' in team.lower()
            
            for stat in statistics:
                stat_type = stat.get('type', '').lower()
                value = stat.get('value', 0)
                
                if value is None:
                    continue
                
                if 'shots on goal' in stat_type or 'shots on target' in stat_type:
                    if is_home:
                        stats_dict['shots_ontarget_home'] = value
                    else:
                        stats_dict['shots_ontarget_away'] = value
                elif 'total shots' in stat_type:
                    if is_home:
                        stats_dict['shots_home'] = value
                    else:
                        stats_dict['shots_away'] = value
                elif 'ball possession' in stat_type:
                    if isinstance(value, str):
                        value = int(value.replace('%', ''))
                    if is_home:
                        stats_dict['possession_home'] = value
                    else:
                        stats_dict['possession_away'] = value
                elif 'corner kicks' in stat_type:
                    if is_home:
                        stats_dict['corners_home'] = value
                    else:
                        stats_dict['corners_away'] = value
        
        stats_dict['has_real_stats'] = any([
            stats_dict['shots_home'] > 0,
            stats_dict['shots_away'] > 0,
            stats_dict['shots_ontarget_home'] > 0,
            stats_dict['shots_ontarget_away'] > 0
        ])
        
        return stats_dict
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


class OptimizedSStatsClient:
    """Оптимизированный клиент для SStats API"""
    
    BASE_URL = "https://api.sstats.net"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.cache = {}
        self.request_times = []
    
    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True) -> Optional[Dict]:
        cache_key = f"{endpoint}_{json.dumps(params) if params else ''}"
        
        if use_cache and cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_time < config.CACHE_TTL:
                return cache_data
        
        url = f"{self.BASE_URL}{endpoint}"
        request_params = {"apikey": self.api_key}
        if params:
            request_params.update(params)
        
        now = datetime.now().timestamp()
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        if len(self.request_times) >= 10:
            wait_time = 1.0 - (now - self.request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        
        try:
            session = await self._get_session()
            async with session.get(url, params=request_params, timeout=timeout) as response:
                self.request_times.append(datetime.now().timestamp())
                
                if response.status == 429:
                    logger.warning("Rate limit exceeded, waiting 2 seconds...")
                    await asyncio.sleep(2)
                    return await self._make_request(endpoint, params, use_cache)
                
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                if use_cache:
                    self.cache[cache_key] = (datetime.now().timestamp(), data)
                
                return data
                
        except Exception as e:
            logger.debug(f"Ошибка запроса: {e}")
            return {"data": []}
    
    async def get_live_matches(self) -> List[Match]:
        params = {"Live": "true", "Limit": 100, "TimeZone": 3}
        # Отключаем кэш для live матчей - всегда свежие данные
        data = await self._make_request("/Games/list", params, use_cache=False)
        return self._parse_matches_list(data) if data else []
    
    async def get_match_statistics(self, match_id: int) -> Optional[Dict]:
        data = await self._make_request(f"/Games/{match_id}", use_cache=False)
        return self._parse_statistics(data) if data else None
    
    def _parse_statistics(self, details: Dict) -> Optional[Dict]:
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
            
            shot_fields = ['Total Shots', 'Shots', 'total_shots', 'shots']
            for field in shot_fields:
                if field in home_stats:
                    shots_home = home_stats.get(field, 0) or 0
                    break
            for field in shot_fields:
                if field in away_stats:
                    shots_away = away_stats.get(field, 0) or 0
                    break
            
            sot_fields = ['Shots on Goal', 'Shots on Target', 'shots_on_target', 'shots_ontarget']
            for field in sot_fields:
                if field in home_stats:
                    shots_on_target_home = home_stats.get(field, 0) or 0
                    break
            for field in sot_fields:
                if field in away_stats:
                    shots_on_target_away = away_stats.get(field, 0) or 0
                    break
            
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
            return None
    
    def _parse_matches_list(self, data: Dict) -> List[Match]:
        matches = []
        games_data = data.get('data', [])
        
        for item in games_data:
            try:
                match = self._parse_game_item(item)
                if match:
                    matches.append(match)
            except Exception:
                continue
        
        return matches
    
    def _parse_game_item(self, item: Dict) -> Optional[Match]:
        match_id = item.get('id')
        if not match_id:
            return None
        
        home_team_data = item.get('homeTeam', {})
        away_team_data = item.get('awayTeam', {})
        
        home_country = None
        away_country = None
        
        if 'country' in home_team_data and isinstance(home_team_data['country'], dict):
            home_country = home_team_data['country'].get('code')
        
        if 'country' in away_team_data and isinstance(away_team_data['country'], dict):
            away_country = away_team_data['country'].get('code')
        
        home_team = Team(
            id=home_team_data.get('id', 0),
            name=home_team_data.get('name', 'Unknown'),
            country_code=home_country
        )
        away_team = Team(
            id=away_team_data.get('id', 0),
            name=away_team_data.get('name', 'Unknown'),
            country_code=away_country
        )
        
        season = item.get('season', {})
        league = season.get('league', {})
        
        return Match(
            id=match_id,
            home_team=home_team,
            away_team=away_team,
            status=item.get('status', 0),
            status_name=item.get('statusName'),
            minute=item.get('elapsed') or 0,
            home_score=item.get('homeResult') or 0,
            away_score=item.get('awayResult') or 0,
            league_id=league.get('id'),
            league_name=league.get('name')
        )
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


class UnifiedFastClient:
    """Унифицированный быстрый клиент для всех API"""
    
    def __init__(self):
        self.sstats = OptimizedSStatsClient(config.SSTATS_TOKEN) if config.SSTATS_TOKEN else None
        self.rapidapi = None
        self.use_mock = config.USE_MOCK_API
    
    async def get_live_matches(self) -> List[Match]:
        matches = []
        tasks = []
        
        if self.sstats and not self.use_mock:
            tasks.append(self.sstats.get_live_matches())
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Ошибка в API: {result}")
                elif result:
                    matches.extend(result)
        
        seen_ids = set()
        unique_matches = []
        for match in matches:
            if match.id not in seen_ids:
                seen_ids.add(match.id)
                unique_matches.append(match)
        
        return unique_matches
    
    async def get_match_statistics(self, match: Match) -> Optional[Dict]:
        if self.sstats and not self.use_mock:
            stats = await self.sstats.get_match_statistics(match.id)
            if stats and stats.get('has_real_stats', False):
                return stats
        
        return {
            'shots_home': 0, 'shots_away': 0,
            'shots_ontarget_home': 0, 'shots_ontarget_away': 0,
            'possession_home': 50, 'possession_away': 50,
            'corners_home': 0, 'corners_away': 0,
            'xg_home': 0.5, 'xg_away': 0.5,
            'has_real_stats': False
        }
    
    async def close(self):
        if self.sstats:
            await self.sstats.close()
        if self.rapidapi:
            await self.rapidapi.close()