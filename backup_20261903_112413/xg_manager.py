# xg_manager.py
import logging
from typing import Optional, Dict
from datetime import datetime
from models import XGData
from xg_provider_football_data import FootballDataXGProvider

logger = logging.getLogger(__name__)

class XGManager:
    """Менеджер для работы с xG"""
    
    def __init__(self, football_data_api_key: str):
        self.provider = FootballDataXGProvider(football_data_api_key)
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
    
    async def get_xg(self, match_id: int, 
                     home_team: Optional[str] = None,
                     away_team: Optional[str] = None,
                     league_id: Optional[int] = None,
                     match_date: Optional[datetime] = None,
                     football_data_id: Optional[int] = None) -> Optional[XGData]:
        """Получает xG из football-data.org"""
        self.stats['total_requests'] += 1
        
        competition_code = None
        if league_id:
            competition_code = self.provider.get_league_code(league_id)
        
        xg_data = await self.provider.get_match_xg(
            match_id=match_id,
            football_data_id=football_data_id,
            home_team=home_team,
            away_team=away_team,
            competition_code=competition_code,
            match_date=match_date
        )
        
        if xg_data:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        return xg_data
    
    async def close(self):
        """Закрывает соединения"""
        await self.provider.close()
    
    def get_stats(self) -> Dict:
        """Возвращает статистику"""
        provider_stats = self.provider.get_stats()
        return {
            'total_requests': self.stats['total_requests'],
            'successful': self.stats['successful_requests'],
            'failed': self.stats['failed_requests'],
            'rate_limit_remaining': provider_stats.get('rate_limit_remaining'),
            'provider_stats': provider_stats
        }