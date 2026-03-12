# xg_provider.py
import aiohttp
import asyncio
import json
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class XGProvider:
    """Провайдер для получения xG (Expected Goals) с Understat.com"""
    
    # Поддержка разных типов матчей
    UNDERSTAT_URLS = {
        'match': "https://understat.com/match/{match_id}",
        'league': "https://understat.com/league/{league_name}",
        'team': "https://understat.com/team/{team_name}"
    }
    
    # Маппинг популярных лиг для Understat
    LEAGUE_MAPPING = {
        2: 'EPL',        # Англия
        4: 'La_liga',     # Испания  
        5: 'Bundesliga',  # Германия
        6: 'Serie_A',     # Италия
        7: 'Ligue_1',     # Франция
        8: 'RFPL'         # Россия
    }
    
    def __init__(self, cache_ttl: int = 3600):  # Кэш на 1 час
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_delay = 2  # Задержка между запросами (уважаем сервер)
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_cache_key(self, match_id: int) -> str:
        """Создает ключ для кэша"""
        return f"xg_{match_id}"
    
    def _get_from_cache(self, match_id: int) -> Optional[Dict]:
        """Получает данные из кэша"""
        cache_key = self._get_cache_key(match_id)
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"xG для матча {match_id} получен из кэша")
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, match_id: int, data: Dict):
        """Сохраняет данные в кэш"""
        cache_key = self._get_cache_key(match_id)
        self.cache[cache_key] = (data, time.time())
        logger.debug(f"xG для матча {match_id} сохранен в кэш")
    
    async def _wait_for_rate_limit(self):
        """Соблюдает rate limiting"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            logger.debug(f"Ожидание {wait_time:.1f}с перед запросом к Understat")
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
    
    async def get_match_xg(self, match_id: int, 
                           understat_match_id: Optional[int] = None) -> Optional[Dict]:
        """
        Получает xG для матча.
        
        Args:
            match_id: ID матча в SStats
            understat_match_id: ID матча в Understat (если известен)
            
        Returns:
            Dict с xG данными или None
        """
        # Проверяем кэш
        cached = self._get_from_cache(match_id)
        if cached:
            return cached
        
        # Пробуем получить xG
        xg_data = None
        
        # Если знаем understat_match_id, используем прямой запрос
        if understat_match_id:
            xg_data = await self._fetch_match_xg(understat_match_id)
        
        # Если не получили, пробуем найти матч через другие методы
        if not xg_data:
            xg_data = await self._find_match_xg(match_id)
        
        if xg_data:
            self._save_to_cache(match_id, xg_data)
            logger.info(f"✅ xG для матча {match_id}: {xg_data.get('home_xg'):.2f}-{xg_data.get('away_xg'):.2f}")
        else:
            logger.debug(f"❌ xG для матча {match_id} не найден")
        
        return xg_data
    
    async def _fetch_match_xg(self, understat_match_id: int) -> Optional[Dict]:
        """Запрашивает xG с конкретной страницы матча Understat"""
        try:
            await self._wait_for_rate_limit()
            
            session = await self._get_session()
            url = self.UNDERSTAT_URLS['match'].format(match_id=understat_match_id)
            
            logger.debug(f"Запрос xG с Understat: {url}")
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"Understat ответил {response.status} для {understat_match_id}")
                    return None
                
                html = await response.text()
                
            # Парсим xG данные из JavaScript переменных
            return self._parse_xg_from_html(html)
            
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к Understat для {understat_match_id}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при запросе xG: {e}")
            return None
    
    async def _find_match_xg(self, sstats_match_id: int) -> Optional[Dict]:
        """
        Пытается найти xG для матча по косвенным данным.
        Сейчас возвращает None, но здесь можно реализовать поиск по дате/командам.
        """
        # TODO: Реализовать поиск матча по дате и командам
        # Это потребует отдельного эндпоинта Understat для поиска
        return None
    
    def _parse_xg_from_html(self, html: str) -> Optional[Dict]:
        """
        Парсит xG данные из HTML страницы Understat.
        Извлекает данные из JavaScript переменных.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем скрипт с данными матча
            scripts = soup.find_all('script')
            xg_data = None
            
            for script in scripts:
                if not script.string:
                    continue
                    
                # Ищем переменную shotsData
                if 'shotsData' in script.string:
                    # Извлекаем JSON
                    match = re.search(r'JSON\.parse\(\'(.+?)\'\)', script.string)
                    if match:
                        try:
                            # Декодируем JSON строку
                            json_str = match.group(1).encode('utf-8').decode('unicode_escape')
                            data = json.loads(json_str)
                            
                            # Рассчитываем суммарный xG
                            home_xg = 0
                            away_xg = 0
                            
                            for shot in data:
                                xg = float(shot.get('xG', 0))
                                if shot.get('h_a') == 'h':
                                    home_xg += xg
                                else:
                                    away_xg += xg
                            
                            xg_data = {
                                'home_xg': round(home_xg, 2),
                                'away_xg': round(away_xg, 2),
                                'total_xg': round(home_xg + away_xg, 2),
                                'shots': len(data),
                                'shots_data': data  # Полные данные по ударам
                            }
                            break
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга JSON: {e}")
                            continue
                
                # Альтернативный источник - teamsData
                elif 'teamsData' in script.string and not xg_data:
                    match = re.search(r'teamsData\s*=\s*(\{.+?\});', script.string)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            # Парсим xG из данных команд
                            home_xg = 0
                            away_xg = 0
                            
                            for team_id, team_data in data.items():
                                if 'xG' in team_data:
                                    if team_data.get('h_a') == 'h':
                                        home_xg += float(team_data['xG'])
                                    else:
                                        away_xg += float(team_data['xG'])
                            
                            xg_data = {
                                'home_xg': round(home_xg, 2),
                                'away_xg': round(away_xg, 2),
                                'total_xg': round(home_xg + away_xg, 2)
                            }
                            break
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга teamsData: {e}")
                            continue
            
            if xg_data:
                logger.debug(f"Распарсены xG: home={xg_data['home_xg']}, away={xg_data['away_xg']}")
            
            return xg_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return None
    
    def get_league_name(self, league_id: Optional[int]) -> Optional[str]:
        """Преобразует ID лиги SStats в название лиги Understat"""
        if league_id and league_id in self.LEAGUE_MAPPING:
            return self.LEAGUE_MAPPING[league_id]
        return None


class XGManager:
    """Менеджер для работы с xG, объединяющий несколько источников"""
    
    def __init__(self):
        self.providers = {
            'understat': XGProvider()
        }
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'cached_requests': 0,
            'failed_requests': 0
        }
    
    async def get_xg(self, match_id: int, 
                     understat_id: Optional[int] = None) -> Optional[Dict]:
        """Получает xG из доступных источников"""
        self.stats['total_requests'] += 1
        
        # Пробуем Understat
        xg_data = await self.providers['understat'].get_match_xg(match_id, understat_id)
        
        if xg_data:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        return xg_data
    
    async def close(self):
        """Закрывает все соединения"""
        for provider in self.providers.values():
            await provider.close()
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы"""
        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'cached_requests': self.stats.get('cached_requests', 0),
            'success_rate': (self.stats['successful_requests'] / 
                           max(1, self.stats['total_requests']) * 100)
        }