# mock_data.py
from datetime import datetime, timedelta
from models import Match, Team, Prediction
import random

class MockDataProvider:
    """Предоставляет тестовые данные для разработки и тестирования"""
    
    @staticmethod
    def get_live_matches() -> list:
        """Возвращает тестовые LIVE матчи"""
        matches = []
        
        # Создаем несколько тестовых матчей
        test_matches = [
            {
                'id': 1001,
                'home': 'Манчестер Сити',
                'away': 'Ливерпуль',
                'home_score': 1,
                'away_score': 1,
                'minute': 67,
                'league': 'АПЛ'
            },
            {
                'id': 1002,
                'home': 'Реал Мадрид',
                'away': 'Барселона',
                'home_score': 2,
                'away_score': 0,
                'minute': 34,
                'league': 'Ла Лига'
            },
            {
                'id': 1003,
                'home': 'Бавария',
                'away': 'Боруссия Д',
                'home_score': 0,
                'away_score': 0,
                'minute': 12,
                'league': 'Бундеслига'
            },
            {
                'id': 1004,
                'home': 'ПСЖ',
                'away': 'Марсель',
                'home_score': 2,
                'away_score': 1,
                'minute': 78,
                'league': 'Лига 1'
            },
            {
                'id': 1005,
                'home': 'Ювентус',
                'away': 'Милан',
                'home_score': 0,
                'away_score': 0,
                'minute': 23,
                'league': 'Серия А'
            }
        ]
        
        for m in test_matches:
            match = Match(
                id=m['id'],
                home_team=Team(id=m['id']*2, name=m['home']),
                away_team=Team(id=m['id']*2+1, name=m['away']),
                status=2,  # LIVE
                minute=m['minute'],
                home_score=m['home_score'],
                away_score=m['away_score'],
                league_name=m['league'],
                start_time=datetime.now() - timedelta(minutes=m['minute']),
                stats={}
            )
            matches.append(match)
        
        return matches
    
    @staticmethod
    def get_today_matches() -> list:
        """Возвращает тестовые матчи на сегодня"""
        matches = MockDataProvider.get_live_matches()
        
        # Добавляем предстоящие матчи
        upcoming = [
            {
                'id': 2001,
                'home': 'Арсенал',
                'away': 'Челси',
                'league': 'АПЛ',
                'time': '19:45'
            },
            {
                'id': 2002,
                'home': 'Атлетико',
                'away': 'Севилья',
                'league': 'Ла Лига',
                'time': '21:00'
            },
            {
                'id': 2003,
                'home': 'Наполи',
                'away': 'Рома',
                'league': 'Серия А',
                'time': '20:45'
            }
        ]
        
        for m in upcoming:
            match = Match(
                id=m['id'],
                home_team=Team(id=m['id']*2, name=m['home']),
                away_team=Team(id=m['id']*2+1, name=m['away']),
                status=1,  # Scheduled
                minute=None,
                home_score=0,
                away_score=0,
                league_name=m['league'],
                start_time=datetime.now().replace(hour=int(m['time'].split(':')[0]), minute=int(m['time'].split(':')[1])),
                stats={}
            )
            matches.append(match)
        
        return matches
    
    @staticmethod
    def get_match_events(match_id: int) -> list:
        """Возвращает тестовые события матча"""
        events = []
        
        # Генерируем случайные события
        num_events = random.randint(3, 8)
        for i in range(num_events):
            minute = random.randint(1, 90)
            event_type = random.choice(['goal', 'shot', 'shot_on_target', 'foul', 'corner'])
            team = 'home' if random.random() > 0.5 else 'away'
            
            events.append({
                'id': i,
                'minute': minute,
                'type': event_type,
                'team': team,
                'player': f'Player {i}'
            })
        
        # Сортируем по минуте
        events.sort(key=lambda x: x['minute'])
        return events
    
    @staticmethod
    def get_match_statistics(match_id: int) -> dict:
        """Возвращает тестовую статистику матча"""
        return {
            'possession': {
                'home': random.randint(45, 65),
                'away': random.randint(35, 55)
            },
            'shots': {
                'home': random.randint(5, 15),
                'away': random.randint(3, 12)
            },
            'shots_on_target': {
                'home': random.randint(2, 8),
                'away': random.randint(1, 6)
            },
            'corners': {
                'home': random.randint(2, 7),
                'away': random.randint(1, 5)
            },
            'fouls': {
                'home': random.randint(5, 12),
                'away': random.randint(5, 12)
            }
        }