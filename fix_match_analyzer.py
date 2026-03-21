# fix_match_analyzer.py
"""
Создание исправленной версии match_analyzer.py
"""

content = '''# match_analyzer.py
"""
Улучшенный анализатор футбольных матчей для прогнозирования голов
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MatchAnalyzer:
    """
    Класс для глубокого анализа матчей и отбора наиболее перспективных
    """
    
    def __init__(self):
        self.weights = {
            'xg': 0.25,
            'shots_accuracy': 0.15,
            'pressure_index': 0.15,
            'form_trend': 0.12,
            'h2h_dominance': 0.10,
            'league_tempo': 0.08,
            'time_remaining': 0.08,
            'score_diff': 0.07,
        }
        
        self.league_thresholds = {
            'top': {'min_xg': 1.2, 'min_shots': 12, 'min_corners': 5, 'goal_probability': 0.45},
            'medium': {'min_xg': 1.0, 'min_shots': 10, 'min_corners': 4, 'goal_probability': 0.42},
            'low': {'min_xg': 0.8, 'min_shots': 8, 'min_corners': 3, 'goal_probability': 0.38}
        }
        
        self.league_stats = defaultdict(lambda: {
            'avg_xg': 1.0, 'avg_shots': 10, 'avg_corners': 4, 'goal_rate': 2.5, 'matches_analyzed': 0
        })
    
    def analyze_match_potential(self, match, home_stats, away_stats, home_form, away_form, h2h_data):
        """Комплексный анализ потенциала матча на гол"""
        try:
            xg_total = home_stats.get('xg', 0) + away_stats.get('xg', 0)
            shots_total = home_stats.get('shots', 0) + away_stats.get('shots', 0)
            shots_ontarget_total = home_stats.get('shots_on_target', 0) + away_stats.get('shots_on_target', 0)
            
            shots_accuracy = shots_ontarget_total / max(shots_total, 1)
            pressure_index = self._calculate_pressure_index(home_stats, away_stats)
            form_trend = self._calculate_form_trend(home_form, away_form)
            h2h_dominance = self._calculate_h2h_dominance(h2h_data)
            league_factor = self._get_league_factor(match)
            time_factor = self._calculate_time_factor(match.minute)
            score_factor = self._calculate_score_factor(match.home_score, match.away_score)
            
            factors = {
                'xg_total': xg_total,
                'shots_accuracy': shots_accuracy,
                'pressure_index': pressure_index,
                'form_trend': form_trend,
                'h2h_dominance': h2h_dominance,
                'league_factor': league_factor,
                'time_factor': time_factor,
                'score_factor': score_factor
            }
            
            total_score = self._calculate_total_score(factors)
            match_level = self._determine_match_level(total_score, match.league_id)
            recommendation = self._get_recommendation(total_score, factors, match)
            
            return {
                'total_score': total_score,
                'match_level': match_level,
                'recommendation': recommendation,
                'factors': factors,
                'should_analyze': total_score >= 0.45,
                'priority': self._get_priority(total_score)
            }
        except Exception as e:
            logger.error(f"Ошибка анализа матча: {e}")
            return {'total_score': 0.3, 'match_level': 'LOW', 'recommendation': 'ANALYZE', 'should_analyze': False, 'priority': 0}
    
    def _calculate_pressure_index(self, home_stats, away_stats):
        home_pressure = home_stats.get('shots', 0) * 0.4 + home_stats.get('corners', 0) * 0.3 + home_stats.get('dangerous_attacks', 0) * 0.3
        away_pressure = away_stats.get('shots', 0) * 0.4 + away_stats.get('corners', 0) * 0.3 + away_stats.get('dangerous_attacks', 0) * 0.3
        total_pressure = home_pressure + away_pressure
        return min(total_pressure / 50, 1.0)
    
    def _calculate_form_trend(self, home_form, away_form):
        if not home_form or not away_form:
            return 0.5
        return (home_form.get('weighted_form', 0.5) + away_form.get('weighted_form', 0.5)) / 2
    
    def _calculate_h2h_dominance(self, h2h_data):
        if not h2h_data or h2h_data.get('matches_played', 0) < 3:
            return 0.5
        total_goals = h2h_data.get('total_goals', 0)
        matches = h2h_data.get('matches_played', 1)
        return min(total_goals / matches / 3, 1.0)
    
    def _get_league_factor(self, match):
        if not match.league_id:
            return 1.0
        league_stats = self.league_stats[match.league_id]
        return min(league_stats['goal_rate'] / 3, 1.2)
    
    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор времени с исключением плохих минут"""
        if not minute:
            return 1.0
        
        # Исключаем плохие минуты (0-10 и 85-90)
        if minute < 10:
            return 0.3
        elif minute < 15:
            return 0.7
        elif minute < 30:
            return 0.85
        elif minute < 45:
            return 0.9
        elif minute < 60:
            return 0.95
        elif minute < 75:
            return 1.0
        elif minute < 85:
            return 1.1
        elif minute < 90:
            return 0.8
        else:
            return 0.5
    
    def _calculate_score_factor(self, home_score, away_score):
        diff = abs((home_score or 0) - (away_score or 0))
        if diff == 0:
            return 1.2
        elif diff == 1:
            return 1.0
        elif diff == 2:
            return 0.7
        else:
            return 0.3
    
    def _calculate_total_score(self, factors):
        score = 0
        total_weight = 0
        weights_map = {
            'xg_total': 0.20, 'shots_accuracy': 0.15, 'pressure_index': 0.15,
            'form_trend': 0.12, 'h2h_dominance': 0.10, 'league_factor': 0.10,
            'time_factor': 0.10, 'score_factor': 0.08
        }
        for key, weight in weights_map.items():
            if key in factors:
                score += factors[key] * weight
                total_weight += weight
        return score / total_weight if total_weight > 0 else 0.5
    
    def _determine_match_level(self, score, league_id):
        if score >= 0.65:
            return "VERY_HIGH"
        elif score >= 0.55:
            return "HIGH"
        elif score >= 0.45:
            return "MEDIUM"
        elif score >= 0.35:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _get_recommendation(self, score, factors, match):
        if score >= 0.6:
            return "STRONG_ANALYZE"
        elif score >= 0.5:
            return "ANALYZE"
        elif score >= 0.4:
            return "WATCH"
        else:
            return "SKIP"
    
    def _get_priority(self, score):
        if score >= 0.65:
            return 1
        elif score >= 0.55:
            return 2
        elif score >= 0.45:
            return 3
        elif score >= 0.35:
            return 4
        else:
            return 5


class MatchFilter:
    def __init__(self):
        self.filters = {
            'minute_range': (10, 85),
            'max_score_diff': 2,
            'min_shots_per_team': 3,
            'excluded_leagues': [],
            'preferred_leagues': [],
        }
        self.filter_stats = defaultdict(lambda: {'passed': 0, 'goals': 0})
    
    def should_analyze(self, match):
        if match.minute and (match.minute < self.filters['minute_range'][0] or 
                            match.minute > self.filters['minute_range'][1]):
            return False, f"minute_{match.minute}"
        
        score_diff = abs((match.home_score or 0) - (match.away_score or 0))
        if score_diff > self.filters['max_score_diff']:
            return False, f"score_diff_{score_diff}"
        
        if match.stats:
            home_shots = match.stats.get('shots_home', 0)
            away_shots = match.stats.get('shots_away', 0)
            if home_shots < self.filters['min_shots_per_team'] and away_shots < self.filters['min_shots_per_team']:
                return False, f"low_shots_{home_shots}_{away_shots}"
        
        if match.league_id in self.filters['excluded_leagues']:
            return False, f"excluded_league_{match.league_id}"
        
        return True, "passed"
    
    def update_filter_stats(self, decision, had_goal):
        self.filter_stats[decision]['passed'] += 1
        if had_goal:
            self.filter_stats[decision]['goals'] += 1
'''

with open('match_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ match_analyzer.py исправлен")