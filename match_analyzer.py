# match_analyzer.py
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
        # Веса для разных факторов
        self.weights = {
            'xg': 0.25,              # Ожидаемые голы
            'shots_accuracy': 0.15,   # Точность ударов
            'pressure_index': 0.15,   # Индекс давления
            'form_trend': 0.12,       # Тренд формы
            'h2h_dominance': 0.10,    # Доминирование в личных встречах
            'league_tempo': 0.08,      # Темп лиги
            'time_remaining': 0.08,    # Оставшееся время
            'score_diff': 0.07,        # Разница в счете
        }
        
        # Пороги для разных лиг
        self.league_thresholds = {
            'top': {  # Топ-5 лиг
                'min_xg': 1.2,
                'min_shots': 12,
                'min_corners': 5,
                'goal_probability': 0.45
            },
            'medium': {  # Средние лиги
                'min_xg': 1.0,
                'min_shots': 10,
                'min_corners': 4,
                'goal_probability': 0.42
            },
            'low': {  # Нижние лиги
                'min_xg': 0.8,
                'min_shots': 8,
                'min_corners': 3,
                'goal_probability': 0.38
            }
        }
        
        # Статистика по лигам (будет заполняться)
        self.league_stats = defaultdict(lambda: {
            'avg_xg': 1.0,
            'avg_shots': 10,
            'avg_corners': 4,
            'goal_rate': 2.5,
            'matches_analyzed': 0
        })
        
    def analyze_match_potential(self, match, home_stats: Dict, away_stats: Dict, 
                                home_form: Optional[Dict], away_form: Optional[Dict],
                                h2h_data: Optional[Dict]) -> Dict:
        """
        Комплексный анализ потенциала матча на гол
        """
        try:
            # 1. Базовые метрики
            xg_total = home_stats.get('xg', 0) + away_stats.get('xg', 0)
            shots_total = home_stats.get('shots', 0) + away_stats.get('shots', 0)
            shots_ontarget_total = home_stats.get('shots_on_target', 0) + away_stats.get('shots_on_target', 0)
            
            # 2. Точность ударов
            shots_accuracy = shots_ontarget_total / max(shots_total, 1)
            
            # 3. Индекс давления (удары + угловые + опасные атаки)
            pressure_index = self._calculate_pressure_index(home_stats, away_stats)
            
            # 4. Тренд формы
            form_trend = self._calculate_form_trend(home_form, away_form)
            
            # 5. Доминирование в личных встречах
            h2h_dominance = self._calculate_h2h_dominance(h2h_data)
            
            # 6. Фактор лиги
            league_factor = self._get_league_factor(match)
            
            # 7. Оставшееся время
            time_factor = self._calculate_time_factor(match.minute)
            
            # 8. Разница в счете
            score_factor = self._calculate_score_factor(match.home_score, match.away_score)
            
            # 9. Комбинированный счет
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
            
            # 10. Итоговая оценка
            total_score = self._calculate_total_score(factors)
            
            # 11. Уровень матча
            match_level = self._determine_match_level(total_score, match.league_id)
            
            # 12. Рекомендация
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
            return {
                'total_score': 0.3,
                'match_level': 'LOW',
                'recommendation': 'ANALYZE',
                'should_analyze': False,
                'priority': 0
            }
    
    def _calculate_pressure_index(self, home_stats: Dict, away_stats: Dict) -> float:
        """Рассчитывает индекс давления"""
        home_pressure = (
            home_stats.get('shots', 0) * 0.4 +
            home_stats.get('corners', 0) * 0.3 +
            home_stats.get('dangerous_attacks', 0) * 0.3
        )
        
        away_pressure = (
            away_stats.get('shots', 0) * 0.4 +
            away_stats.get('corners', 0) * 0.3 +
            away_stats.get('dangerous_attacks', 0) * 0.3
        )
        
        total_pressure = home_pressure + away_pressure
        # Нормализация к 0-1
        return min(total_pressure / 50, 1.0)
    
    def _calculate_form_trend(self, home_form: Optional[Dict], away_form: Optional[Dict]) -> float:
        """Рассчитывает тренд формы команд"""
        if not home_form or not away_form:
            return 0.5
        
        home_trend = home_form.get('weighted_form', 0.5)
        away_trend = away_form.get('weighted_form', 0.5)
        
        # Чем выше форма обеих команд, тем выше вероятность гола
        return (home_trend + away_trend) / 2
    
    def _calculate_h2h_dominance(self, h2h_data: Optional[Dict]) -> float:
        """Рассчитывает доминирование в личных встречах"""
        if not h2h_data or h2h_data.get('matches_played', 0) < 3:
            return 0.5
        
        total_goals = h2h_data.get('total_goals', 0)
        matches = h2h_data.get('matches_played', 1)
        avg_goals = total_goals / matches
        
        # Нормализация: 0-3 голов -> 0-1
        return min(avg_goals / 3, 1.0)
    
    def _get_league_factor(self, match) -> float:
        """Определяет фактор лиги"""
        if not match.league_id:
            return 1.0
        
        league_stats = self.league_stats[match.league_id]
        goal_rate = league_stats['goal_rate']
        
        # Чем выше результативность лиги, тем выше фактор
        return min(goal_rate / 3, 1.2)
    
    def _calculate_time_factor(self, minute: int) -> float:
        """Рассчитывает фактор оставшегося времени"""
        if not minute:
            return 1.0
        
        # Пик активности: 70-85 минуты
        if minute < 45:
            return 0.8  # Первый тайм
        elif minute < 70:
            return 1.0  # Начало второго
        elif minute < 85:
            return 1.3  # Самые опасные минуты
        else:
            return 0.7  # Концовка
    
    def _calculate_score_factor(self, home_score: int, away_score: int) -> float:
        """Рассчитывает фактор разницы в счете"""
        diff = abs((home_score or 0) - (away_score or 0))
        
        if diff == 0:
            return 1.2  # Ничья - высокая вероятность
        elif diff == 1:
            return 1.0  # Минимальная разница
        elif diff == 2:
            return 0.7  # Средняя разница
        else:
            return 0.3  # Большая разница - матч решен
    
    def _calculate_total_score(self, factors: Dict) -> float:
        """Рассчитывает итоговую оценку"""
        score = 0
        total_weight = 0
        
        weights_map = {
            'xg_total': 0.20,
            'shots_accuracy': 0.15,
            'pressure_index': 0.15,
            'form_trend': 0.12,
            'h2h_dominance': 0.10,
            'league_factor': 0.10,
            'time_factor': 0.10,
            'score_factor': 0.08
        }
        
        for key, weight in weights_map.items():
            if key in factors:
                score += factors[key] * weight
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.5
    
    def _determine_match_level(self, score: float, league_id: Optional[int]) -> str:
        """Определяет уровень матча"""
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
    
    def _get_recommendation(self, score: float, factors: Dict, match) -> str:
        """Дает рекомендацию по матчу"""
        if score >= 0.6:
            return "STRONG_ANALYZE"
        elif score >= 0.5:
            return "ANALYZE"
        elif score >= 0.4:
            return "WATCH"
        else:
            return "SKIP"
    
    def _get_priority(self, score: float) -> int:
        """Возвращает приоритет анализа (1-5)"""
        if score >= 0.65:
            return 1  # Высший приоритет
        elif score >= 0.55:
            return 2
        elif score >= 0.45:
            return 3
        elif score >= 0.35:
            return 4
        else:
            return 5  # Низший приоритет
    
    def update_league_stats(self, match):
        """Обновляет статистику по лиге"""
        if not match.league_id or not match.is_finished:
            return
        
        stats = self.league_stats[match.league_id]
        total_matches = stats['matches_analyzed']
        
        # Обновляем средние значения
        if match.stats:
            stats['avg_xg'] = (stats['avg_xg'] * total_matches + match.stats.get('xg_total', 1.0)) / (total_matches + 1)
            stats['avg_shots'] = (stats['avg_shots'] * total_matches + match.stats.get('shots_total', 10)) / (total_matches + 1)
        
        stats['goal_rate'] = (stats['goal_rate'] * total_matches + (match.home_score + match.away_score)) / (total_matches + 1)
        stats['matches_analyzed'] += 1


class MatchFilter:
    """
    Класс для фильтрации матчей перед анализом
    """
    
    def __init__(self):
        self.filters = {
            'minute_range': (10, 85),        # Анализируем только с 10 по 85 минуту
            'max_score_diff': 2,               # Максимальная разница в счете
            'min_shots_per_team': 3,            # Минимум ударов у команды
            'excluded_leagues': [],             # Исключенные лиги
            'preferred_leagues': [],            # Предпочитаемые лиги
        }
        
        # Статистика эффективности фильтров
        self.filter_stats = defaultdict(lambda: {'passed': 0, 'goals': 0})
    
    def should_analyze(self, match) -> Tuple[bool, str]:
        """
        Проверяет, стоит ли анализировать матч
        Возвращает (решение, причина)
        """
        
        # 1. Проверка минуты
        if match.minute and (match.minute < self.filters['minute_range'][0] or 
                            match.minute > self.filters['minute_range'][1]):
            return False, f"minute_{match.minute}"
        
        # 2. Проверка разницы в счете
        score_diff = abs((match.home_score or 0) - (match.away_score or 0))
        if score_diff > self.filters['max_score_diff']:
            return False, f"score_diff_{score_diff}"
        
        # 3. Проверка статистики (если есть)
        if match.stats:
            home_shots = match.stats.get('shots_home', 0)
            away_shots = match.stats.get('shots_away', 0)
            
            if home_shots < self.filters['min_shots_per_team'] and away_shots < self.filters['min_shots_per_team']:
                return False, f"low_shots_{home_shots}_{away_shots}"
        
        # 4. Проверка исключенных лиг
        if match.league_id in self.filters['excluded_leagues']:
            return False, f"excluded_league_{match.league_id}"
        
        return True, "passed"
    
    def update_filter_stats(self, decision: str, had_goal: bool):
        """Обновляет статистику фильтров"""
        self.filter_stats[decision]['passed'] += 1
        if had_goal:
            self.filter_stats[decision]['goals'] += 1
    
    def get_filter_efficiency(self) -> Dict:
        """Возвращает эффективность фильтров"""
        efficiency = {}
        for filter_name, stats in self.filter_stats.items():
            if stats['passed'] > 0:
                efficiency[filter_name] = stats['goals'] / stats['passed']
        return efficiency
    
    def optimize_filters(self):
        """Оптимизирует фильтры на основе статистики"""
        # Анализируем, какие фильтры лучше работают
        efficiency = self.get_filter_efficiency()
        
        # Можно автоматически подстраивать пороги
        for minute in range(5, 90, 5):
            key = f"minute_{minute}"
            if key in efficiency and efficiency[key] < 0.1:
                # Если на этой минуте почти нет голов, исключаем её
                logger.info(f"Минута {minute} показывает низкую эффективность ({efficiency[key]:.2f})")