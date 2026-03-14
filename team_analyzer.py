# team_analyzer.py
from typing import Dict, List
from datetime import datetime, timedelta

class TeamAnalyzer:
    """Анализ формы команд и статистики"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_team_form(self, team_id: int, last_n: int = 5) -> Dict:
        """Анализирует форму команды за последние N матчей"""
        # Запрос к базе данных для получения последних матчей
        recent_matches = self.get_recent_matches(team_id, last_n)
        
        if not recent_matches:
            return {'points': 0, 'goals_scored': 0, 'goals_conceded': 0, 'form': 'unknown'}
        
        points = 0
        goals_scored = 0
        goals_conceded = 0
        
        for match in recent_matches:
            is_home = match['home_id'] == team_id
            team_goals = match['home_score'] if is_home else match['away_score']
            opp_goals = match['away_score'] if is_home else match['home_score']
            
            goals_scored += team_goals
            goals_conceded += opp_goals
            
            if team_goals > opp_goals:
                points += 3
            elif team_goals == opp_goals:
                points += 1
        
        # Форма в виде строки (WWDLL)
        form_string = self._get_form_string(recent_matches, team_id)
        
        return {
            'points': points,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'avg_scored': goals_scored / len(recent_matches),
            'avg_conceded': goals_conceded / len(recent_matches),
            'form': form_string,
            'matches_played': len(recent_matches)
        }
    
    def get_h2h_stats(self, team1_id: int, team2_id: int) -> Dict:
        """Анализирует историю личных встреч"""
        h2h_matches = self.get_h2h_matches(team1_id, team2_id, limit=10)
        
        if not h2h_matches:
            return {'home_wins': 0, 'away_wins': 0, 'draws': 0, 'avg_goals': 0}
        
        home_wins = 0
        away_wins = 0
        draws = 0
        total_goals = 0
        
        for match in h2h_matches:
            if match['home_score'] > match['away_score']:
                home_wins += 1
            elif match['home_score'] < match['away_score']:
                away_wins += 1
            else:
                draws += 1
            
            total_goals += match['home_score'] + match['away_score']
        
        return {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'avg_goals': total_goals / len(h2h_matches)
        }
    
    def _get_form_string(self, matches: List[Dict], team_id: int) -> str:
        """Преобразует результаты в строку формы (WDL)"""
        form = []
        for match in matches:
            is_home = match['home_id'] == team_id
            team_goals = match['home_score'] if is_home else match['away_score']
            opp_goals = match['away_score'] if is_home else match['home_score']
            
            if team_goals > opp_goals:
                form.append('W')
            elif team_goals < opp_goals:
                form.append('L')
            else:
                form.append('D')
        
        return ''.join(form)