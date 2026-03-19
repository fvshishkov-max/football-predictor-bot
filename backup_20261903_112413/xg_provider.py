# xg_provider.py
import aiohttp
import asyncio
import json
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime
from bs4 import BeautifulSoup
import time
from cachetools import TTLCache

from models import XGData  # Импортируем новый класс

logger = logging.getLogger(__name__)

class XGProvider:
    """Провайдер для получения xG (Expected Goals) с Understat.com"""
    
    UNDERSTAT_URL = "https://understat.com/match/{match_id}"
    
    # Маппинг лиг SStats -> Understat
    LEAGUE_MAPPING = {
        2: 'EPL',        # Английская Премьер-лига
        3: 'EPL',        # Чемпионшип (тоже England)
        4: 'La_liga',    # Испания
        5: 'Bundesliga', # Германия
        6: 'Serie_A',    # Италия
        7: 'Ligue_1',    # Франция
        8: 'RFPL',       # Россия
        9: 'RFPL',       # Россия (ФНЛ)
        13: 'EPL',       # АПЛ (дополнительно)
        19: 'Serie_A',   # Серия А
        20: 'Bundesliga', # Бундеслига
        21: 'La_liga',   # Ла Лига
        22: 'Ligue_1',   # Лига 1
    }
    
    def __init__(self, cache_ttl: int = 3600):  # Кэш на 1 час
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_delay = 3  # Увеличим до 3 секунд (уважаем сервер)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0
        }
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
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
            logger.debug(f"Ожидание {wait_time:.1f}с перед запросом к Understat")
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
    
    async def get_match_xg(self, match_id: int, understat_id: Optional[int] = None) -> Optional[XGData]:
        """
        Получает xG для матча.
        
        Args:
            match_id: ID матча в SStats (для кэша)
            understat_id: ID матча в Understat (если известен)
            
        Returns:
            XGData объект с xG данными или None
        """
        self.stats['total_requests'] += 1
        
        # Проверяем кэш
        cache_key = f"xg_{match_id}"
        if cache_key in self.cache:
            self.stats['cached_requests'] += 1
            logger.debug(f"xG для матча {match_id} получен из кэша")
            return self.cache[cache_key]
        
        if not understat_id:
            logger.debug(f"Нет understat_id для матча {match_id}")
            return None
        
        try:
            await self._wait_for_rate_limit()
            
            session = await self._get_session()
            url = self.UNDERSTAT_URL.format(match_id=understat_id)
            
            logger.info(f"Запрос xG с Understat: {url}")
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Understat ответил {response.status} для {understat_id}")
                    self.stats['failed_requests'] += 1
                    return None
                
                html = await response.text()
            
            # Парсим xG данные
            xg_data = self._parse_xg_from_html(html, understat_id)
            
            if xg_data:
                self.stats['successful_requests'] += 1
                self.cache[cache_key] = xg_data
                logger.info(f"✅ xG для матча {match_id}: {xg_data.home_xg:.2f}-{xg_data.away_xg:.2f} (всего {xg_data.total_xg:.2f})")
                return xg_data
            else:
                self.stats['failed_requests'] += 1
                logger.warning(f"Не удалось распарсить xG для матча {understat_id}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к Understat для {understat_id}")
            self.stats['failed_requests'] += 1
            return None
        except Exception as e:
            logger.error(f"Ошибка при запросе xG: {e}")
            self.stats['failed_requests'] += 1
            return None
    
    def _parse_xg_from_html(self, html: str, understat_id: int) -> Optional[XGData]:
        """
        Парсит xG данные из HTML страницы Understat.
        Возвращает объект XGData.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Ищем скрипт с данными
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                    
                # Ищем переменную shotsData
                if 'shotsData' in script.string:
                    # Извлекаем JSON
                    match = re.search(r'var shotsData\s*=\s*JSON\.parse\(\'(.+?)\'\)', script.string, re.DOTALL)
                    if match:
                        try:
                            # Декодируем JSON строку
                            json_str = match.group(1).encode('utf-8').decode('unicode_escape')
                            data = json.loads(json_str)
                            
                            # Рассчитываем суммарный xG
                            home_xg = 0.0
                            away_xg = 0.0
                            
                            for shot in data:
                                try:
                                    xg = float(shot.get('xG', 0))
                                    if shot.get('h_a') == 'h':
                                        home_xg += xg
                                    else:
                                        away_xg += xg
                                except (ValueError, TypeError):
                                    continue
                            
                            return XGData(
                                home_xg=round(home_xg, 2),
                                away_xg=round(away_xg, 2),
                                total_xg=round(home_xg + away_xg, 2),
                                shots=len(data),
                                source='shotsData',
                                understat_id=understat_id
                            )
                            
                        except json.JSONDecodeError as e:
                            logger.debug(f"Ошибка парсинга JSON shotsData: {e}")
                            continue
                
                # Альтернативный источник - teamsData
                elif 'teamsData' in script.string:
                    match = re.search(r'var teamsData\s*=\s*(\{.+?\});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            
                            home_xg = 0.0
                            away_xg = 0.0
                            
                            for team_id, team_data in data.items():
                                if 'xg' in team_data:
                                    try:
                                        if team_data.get('h_a') == 'h':
                                            home_xg += float(team_data['xg'])
                                        else:
                                            away_xg += float(team_data['xg'])
                                    except (ValueError, TypeError):
                                        continue
                            
                            return XGData(
                                home_xg=round(home_xg, 2),
                                away_xg=round(away_xg, 2),
                                total_xg=round(home_xg + away_xg, 2),
                                source='teamsData',
                                understat_id=understat_id
                            )
                            
                        except json.JSONDecodeError as e:
                            logger.debug(f"Ошибка парсинга JSON teamsData: {e}")
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return None
    
    def get_league_name(self, league_id: Optional[int]) -> Optional[str]:
        """Преобразует ID лиги SStats в название лиги Understat"""
        if league_id and league_id in self.LEAGUE_MAPPING:
            return self.LEAGUE_MAPPING[league_id]
        return None
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы"""
        total = self.stats['total_requests']
        return {
            'total_requests': total,
            'successful': self.stats['successful_requests'],
            'failed': self.stats['failed_requests'],
            'cached': self.stats['cached_requests'],
            'success_rate': round((self.stats['successful_requests'] / max(1, total)) * 100, 1)
        }


class XGManager:
    """Менеджер для работы с xG, объединяющий несколько источников"""
    
    def __init__(self):
        self.providers = {
            'understat': XGProvider()
        }
        from understat_search import UnderstatSearch
        self.searcher = UnderstatSearch()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cached_requests': 0,
            'search_requests': 0,
            'successful_searches': 0
        }
    
    async def get_xg(self, match_id: int, understat_id: Optional[int] = None,
                     home_team: Optional[str] = None, away_team: Optional[str] = None,
                     league: Optional[str] = None, match_date: Optional[datetime] = None) -> Optional[XGData]:
        """
        Получает xG с автоматическим поиском understat_id.
        Возвращает объект XGData.
        """
        self.stats['total_requests'] += 1
        
        # Если understat_id не указан, пробуем найти
        if not understat_id and home_team and away_team and league and match_date:
            self.stats['search_requests'] += 1
            found_id = await self.searcher.find_match(
                home_team, away_team, league, match_date
            )
            if found_id:
                self.stats['successful_searches'] += 1
                understat_id = found_id
                logger.info(f"🔍 Найден understat_id {understat_id} для матча {match_id}")
        
        # Получаем xG
        xg_data = await self.providers['understat'].get_match_xg(match_id, understat_id)
        
        if xg_data:
            self.stats['successful_requests'] += 1
            # Обновляем статистику провайдера
            provider_stats = self.providers['understat'].get_stats()
            self.stats['cached_requests'] = provider_stats.get('cached', 0)
        else:
            self.stats['failed_requests'] += 1
        
        return xg_data
    
    async def close(self):
        """Закрывает все соединения"""
        for provider in self.providers.values():
            await provider.close()
        await self.searcher.close()
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы"""
        provider_stats = self.providers['understat'].get_stats()
        
        return {
            'total_requests': self.stats['total_requests'],
            'successful': self.stats['successful_requests'],
            'failed': self.stats['failed_requests'],
            'cached': provider_stats.get('cached', 0),
            'search_requests': self.stats['search_requests'],
            'successful_searches': self.stats['successful_searches'],
            'search_success_rate': round((self.stats['successful_searches'] / max(1, self.stats['search_requests'])) * 100, 1),
            'success_rate': round((self.stats['successful_requests'] / max(1, self.stats['total_requests'])) * 100, 1),
            'provider_stats': provider_stats
        }