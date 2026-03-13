# xg_provider_understat_proxy.py
import aiohttp
import asyncio
import logging
import random
from typing import Optional, Dict, List
from datetime import datetime
from models import XGData

logger = logging.getLogger(__name__)

class UnderstatProxyXGProvider:
    """Провайдер xG через Understat с использованием прокси"""
    
    UNDERSTAT_URL = "https://understat.com/match/{match_id}"
    
    # Список прокси (можно заменить на свои)
    PROXIES = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080",
        # Добавьте реальные прокси
    ]
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    def __init__(self, use_proxy: bool = True):
        self.use_proxy = use_proxy
        self.cache = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = None
            if self.use_proxy and self.PROXIES:
                proxy = random.choice(self.PROXIES)
                connector = aiohttp.TCPConnector()
            
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': random.choice(self.USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                connector=connector
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_match_xg(self, understat_id: int) -> Optional[XGData]:
        """Получает xG с Understat через прокси"""
        cache_key = f"understat_{understat_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            session = await self._get_session()
            url = self.UNDERSTAT_URL.format(match_id=understat_id)
            
            logger.info(f"Запрос xG с Understat (ID: {understat_id})")
            
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Understat ответил {response.status}")
                    return None
                
                html = await response.text()
                
                # Здесь нужно добавить парсинг HTML как в xg_provider.py
                # Упрощенная версия:
                import re
                import json
                
                # Ищем данные xG в HTML
                match = re.search(r'var shotsData\s*=\s*JSON\.parse\(\'(.+?)\'\)', html, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1).encode('utf-8').decode('unicode_escape')
                        data = json.loads(json_str)
                        
                        home_xg = sum(float(shot.get('xG', 0)) for shot in data if shot.get('h_a') == 'h')
                        away_xg = sum(float(shot.get('xG', 0)) for shot in data if shot.get('h_a') == 'a')
                        
                        xg_data = XGData(
                            home_xg=round(home_xg, 2),
                            away_xg=round(away_xg, 2),
                            total_xg=round(home_xg + away_xg, 2),
                            source='Understat (proxy)',
                            understat_id=understat_id
                        )
                        
                        self.cache[cache_key] = xg_data
                        logger.info(f"✅ xG получен с Understat: {xg_data.home_xg}-{xg_data.away_xg}")
                        return xg_data
                        
                    except Exception as e:
                        logger.error(f"Ошибка парсинга: {e}")
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка запроса к Understat: {e}")
            return None


class XGProviderAggregator:
    """Агрегатор xG из нескольких источников"""
    
    def __init__(self, football_data_api_key: str):
        from xg_provider_football_data import FootballDataXGProvider
        self.providers = {
            'football_data': FootballDataXGProvider(football_data_api_key),
            'understat_proxy': UnderstatProxyXGProvider(use_proxy=True)
        }
        self.stats = defaultdict(lambda: {'attempts': 0, 'success': 0})
    
    async def get_xg(self, match_id: int, understat_id: Optional[int] = None,
                     **kwargs) -> Optional[XGData]:
        """Получает xG из всех доступных источников"""
        
        # Сначала пробуем Understat
        if understat_id:
            self.stats['understat_proxy']['attempts'] += 1
            xg_data = await self.providers['understat_proxy'].get_match_xg(understat_id)
            if xg_data:
                self.stats['understat_proxy']['success'] += 1
                return xg_data
        
        # Затем football-data.org
        self.stats['football_data']['attempts'] += 1
        xg_data = await self.providers['football_data'].get_match_xg(match_id, **kwargs)
        if xg_data:
            self.stats['football_data']['success'] += 1
            return xg_data
        
        return None
    
    async def close(self):
        for provider in self.providers.values():
            await provider.close()
    
    def get_stats(self) -> Dict:
        return {
            provider: {
                'attempts': self.stats[provider]['attempts'],
                'success': self.stats[provider]['success'],
                'success_rate': (self.stats[provider]['success'] / max(1, self.stats[provider]['attempts'])) * 100
            }
            for provider in self.providers.keys()
        }