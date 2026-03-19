# feature_engineering.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Продвинутый инжиниринг признаков для прогнозирования голов
    Вдохновлено лучшими практиками из futbol_corners_forecast
    """
    
    def __init__(self):
        self.feature_names = []
        self.league_averages = defaultdict(lambda: defaultdict(float))
        
    def set_league_averages(self, league_id: int, averages: Dict):
        """Устанавливает средние показатели по лиге для нормализации"""
        self.league_averages[league_id] = averages
    
    def create_all_features(self, match, home_stats: Dict, away_stats: Dict,
                           home_form: Dict, away_form: Dict, h2h_data: List[Dict],
                           league_id: int) -> np.ndarray:
        """
        Создает полный набор признаков (60+)
        
        Returns:
            np.ndarray: вектор признаков для ML модели
        """
        features = []
        feature_dict = {}
        
        # 1. Базовые признаки команды (нормализованные по лиге)
        league_avg = self.league_averages.get(league_id, {})
        home_basic = self._create_basic_features(home_stats, league_avg, prefix='home_')
        away_basic = self._create_basic_features(away_stats, league_avg, prefix='away_')
        feature_dict.update(home_basic)
        feature_dict.update(away_basic)
        
        # 2. Продвинутые признаки команды
        home_advanced = self._create_advanced_features(home_stats, prefix='home_')
        away_advanced = self._create_advanced_features(away_stats, prefix='away_')
        feature_dict.update(home_advanced)
        feature_dict.update(away_advanced)
        
        # 3. Форма команд (последние 5 матчей)
        form_features = self._create_form_features(home_form, away_form)
        feature_dict.update(form_features)
        
        # 4. История личных встреч
        h2h_features = self._create_h2h_features(h2h_data)
        feature_dict.update(h2h_features)
        
        # 5. Контекст матча
        context_features = self._create_context_features(match, home_stats, away_stats)
        feature_dict.update(context_features)
        
        # 6. Эффективность и индексы
        efficiency_features = self._create_efficiency_indices(home_stats, away_stats)
        feature_dict.update(efficiency_features)
        
        # 7. Динамика матча (для live)
        if match.minute and match.minute > 0:
            dynamic_features = self._create_dynamic_features(match, home_stats, away_stats)
            feature_dict.update(dynamic_features)
        
        # Конвертируем в вектор в фиксированном порядке
        self.feature_names = list(feature_dict.keys())
        features = list(feature_dict.values())
        
        return np.array(features).reshape(1, -1)
    
    def _create_basic_features(self, stats: Dict, league_avg: Dict, prefix: str = '') -> Dict:
        """Создает базовые признаки с нормализацией по лиге (9 признаков)"""
        features = {}
        
        # Ключевые показатели
        basic_stats = {
            'shots': stats.get('shots', 0),
            'shots_on_target': stats.get('shots_on_target', 0),
            'xg': stats.get('xg', 0.5),
            'corners': stats.get('corners', 0),
            'possession': stats.get('possession', 50),
            'dangerous_attacks': stats.get('dangerous_attacks', 0),
            'passes': stats.get('passes', 0),
            'fouls': stats.get('fouls', 0),
            'yellow_cards': stats.get('yellow_cards', 0)
        }
        
        for key, value in basic_stats.items():
            # Само значение
            features[f'{prefix}{key}'] = value
            
            # Нормализованное по лиге (относительная сила)
            league_value = league_avg.get(key, 1)
            if league_value > 0:
                features[f'{prefix}{key}_norm'] = value / league_value
            else:
                features[f'{prefix}{key}_norm'] = 1.0
            
            # Квадратичные признаки (для нелинейностей)
            features[f'{prefix}{key}_squared'] = value ** 2
            
            # Логарифмические (для сглаживания больших значений)
            features[f'{prefix}{key}_log'] = np.log1p(value)
        
        return features
    
    def _create_advanced_features(self, stats: Dict, prefix: str = '') -> Dict:
        """Создает продвинутые составные признаки (15 признаков)"""
        features = {}
        
        shots = stats.get('shots', 1)
        sot = stats.get('shots_on_target', 0)
        xg = stats.get('xg', 0.5)
        possession = stats.get('possession', 50)
        passes = stats.get('passes', 100)
        
        # 1. Точность ударов
        features[f'{prefix}shot_accuracy'] = sot / shots if shots > 0 else 0
        
        # 2. Качество моментов (xG за удар)
        features[f'{prefix}xg_per_shot'] = xg / shots if shots > 0 else 0.1
        
        # 3. Интенсивность атак (опасные атаки на удар)
        dangerous = stats.get('dangerous_attacks', 0)
        features[f'{prefix}attack_intensity'] = dangerous / shots if shots > 0 else 0
        
        # 4. Эффективность владения
        features[f'{prefix}possession_efficiency'] = shots / possession * 100 if possession > 0 else 0
        
        # 5. Созидательная активность (удары с пасов)
        features[f'{prefix}creative_output'] = shots / passes * 100 if passes > 0 else 0
        
        # 6. Опасность стандартов
        corners = stats.get('corners', 0)
        features[f'{prefix}set_piece_danger'] = corners * 0.3  # Угловые конвертируются в голы с вероятностью ~3%
        
        # 7. Дисциплина (фолы и карточки)
        fouls = stats.get('fouls', 0)
        yellow = stats.get('yellow_cards', 0)
        features[f'{prefix}aggression'] = (fouls + yellow * 2) / 10
        
        # 8. Контроль игры (владение + пасы)
        features[f'{prefix}game_control'] = (possession / 100) * (passes / 500)
        
        # 9. Опасные моменты (xG + удары в створ)
        features[f'{prefix}threat_level'] = xg * 2 + sot * 0.3
        
        # 10. Соотношение ударов
        features[f'{prefix}shot_ratio'] = shots / (stats.get('shots_conceded', shots) + 1)
        
        # 11. Конверсия xG
        goals = stats.get('goals', 0)
        features[f'{prefix}xg_conversion'] = goals / xg if xg > 0 else 0
        
        # 12. Давление на вратаря
        features[f'{prefix}goalkeeper_pressure'] = sot / (stats.get('saves', 1) + 1)
        
        # 13. Атакующий импульс
        features[f'{prefix}attack_momentum'] = dangerous / 10
        
        # 14. Игровой ритм
        features[f'{prefix}game_pace'] = (shots + passes/10) / 10
        
        # 15. Интегральный индекс силы
        features[f'{prefix}power_index'] = (
            xg * 0.3 + 
            sot * 0.2 + 
            dangerous * 0.15 + 
            possession/100 * 0.2 + 
            corners * 0.15
        )
        
        return features
    
    def _create_form_features(self, home_form: Dict, away_form: Dict) -> Dict:
        """Создает признаки на основе формы команд (8 признаков)"""
        features = {}
        
        if home_form:
            features['home_points_per_game'] = home_form.get('points_per_game', 1.0)
            features['home_form_trend'] = home_form.get('trend', 0)
            features['home_avg_scored'] = home_form.get('avg_scored', 1.0)
            features['home_avg_conceded'] = home_form.get('avg_conceded', 1.0)
            features['home_avg_xg_for'] = home_form.get('avg_xg_for', 1.0)
            features['home_avg_xg_against'] = home_form.get('avg_xg_against', 1.0)
        else:
            features['home_points_per_game'] = 1.0
            features['home_form_trend'] = 0
            features['home_avg_scored'] = 1.0
            features['home_avg_conceded'] = 1.0
            features['home_avg_xg_for'] = 1.0
            features['home_avg_xg_against'] = 1.0
        
        if away_form:
            features['away_points_per_game'] = away_form.get('points_per_game', 1.0)
            features['away_form_trend'] = away_form.get('trend', 0)
            features['away_avg_scored'] = away_form.get('avg_scored', 1.0)
            features['away_avg_conceded'] = away_form.get('avg_conceded', 1.0)
            features['away_avg_xg_for'] = away_form.get('avg_xg_for', 1.0)
            features['away_avg_xg_against'] = away_form.get('avg_xg_against', 1.0)
        else:
            features['away_points_per_game'] = 1.0
            features['away_form_trend'] = 0
            features['away_avg_scored'] = 1.0
            features['away_avg_conceded'] = 1.0
            features['away_avg_xg_for'] = 1.0
            features['away_avg_xg_against'] = 1.0
        
        # Разница в форме
        features['form_difference'] = features['home_points_per_game'] - features['away_points_per_game']
        
        return features
    
    def _create_h2h_features(self, h2h_data: List[Dict]) -> Dict:
        """Создает признаки из истории встреч (10 признаков)"""
        features = {}
        
        if not h2h_data or h2h_data.get('matches_played', 0) == 0:
            features['h2h_home_advantage'] = 0
            features['h2h_avg_goals'] = 2.5
            features['h2h_home_wins'] = 0.33
            features['h2h_away_wins'] = 0.33
            features['h2h_draws'] = 0.34
            features['h2h_avg_home_goals'] = 1.4
            features['h2h_avg_away_goals'] = 1.1
            features['h2h_avg_xg_home'] = 1.3
            features['h2h_avg_xg_away'] = 1.0
            features['h2h_trend'] = 0
            return features
        
        matches = h2h_data['matches_played']
        
        features['h2h_home_advantage'] = (h2h_data['team1_wins'] - h2h_data['team2_wins']) / matches
        features['h2h_avg_goals'] = (h2h_data['team1_goals'] + h2h_data['team2_goals']) / matches
        features['h2h_home_wins'] = h2h_data['team1_wins'] / matches
        features['h2h_away_wins'] = h2h_data['team2_wins'] / matches
        features['h2h_draws'] = h2h_data['draws'] / matches
        features['h2h_avg_home_goals'] = h2h_data.get('team1_avg_goals', 1.4)
        features['h2h_avg_away_goals'] = h2h_data.get('team2_avg_goals', 1.1)
        features['h2h_avg_xg_home'] = h2h_data.get('team1_avg_xg', 1.3)
        features['h2h_avg_xg_away'] = h2h_data.get('team2_avg_xg', 1.0)
        features['h2h_trend'] = h2h_data.get('trend', 0)
        
        return features
    
    def _create_context_features(self, match, home_stats: Dict, away_stats: Dict) -> Dict:
        """Создает контекстные признаки матча (8 признаков)"""
        features = {}
        
        # Минута матча (нормализованная)
        minute = match.minute or 0
        features['minute_norm'] = minute / 90
        features['minutes_remaining'] = 1 - minute/90
        
        # Счет
        home_score = match.home_score or 0
        away_score = match.away_score or 0
        features['score_difference'] = home_score - away_score
        features['total_goals'] = home_score + away_score
        features['is_home_leading'] = 1 if home_score > away_score else 0
        features['is_away_leading'] = 1 if away_score > home_score else 0
        features['is_draw'] = 1 if home_score == away_score else 0
        
        # Тайм
        features['is_first_half'] = 1 if minute < 45 else 0
        features['is_second_half'] = 1 if minute >= 45 else 0
        
        return features
    
    def _create_efficiency_indices(self, home_stats: Dict, away_stats: Dict) -> Dict:
        """Создает индексы эффективности (5 признаков)"""
        features = {}
        
        # Соотношение xG
        home_xg = home_stats.get('xg', 0.5)
        away_xg = away_stats.get('xg', 0.5)
        features['xg_ratio'] = home_xg / (away_xg + 0.1)
        
        # Соотношение ударов
        home_shots = home_stats.get('shots', 1)
        away_shots = away_stats.get('shots', 1)
        features['shot_ratio'] = home_shots / (away_shots + 0.1)
        
        # Соотношение ударов в створ
        home_sot = home_stats.get('shots_on_target', 0)
        away_sot = away_stats.get('shots_on_target', 0)
        features['sot_ratio'] = (home_sot + 0.1) / (away_sot + 0.1)
        
        # Соотношение владения
        home_pos = home_stats.get('possession', 50)
        away_pos = away_stats.get('possession', 50)
        features['possession_ratio'] = home_pos / (away_pos + 0.1)
        
        # Индекс доминирования
        features['dominance_index'] = (
            (home_xg / (away_xg + 0.1)) * 0.3 +
            (home_shots / (away_shots + 0.1)) * 0.3 +
            (home_pos / 50) * 0.4
        ) / 2
        
        return features
    
    def _create_dynamic_features(self, match, home_stats: Dict, away_stats: Dict) -> Dict:
        """Создает признаки динамики матча (для live)"""
        features = {}
        
        minute = match.minute or 0
        
        # Интенсивность в последние 15 минут
        if minute > 15:
            # В реальности нужно брать статистику последних 15 минут
            # Здесь упрощенная версия
            features['recent_intensity'] = (home_stats.get('shots', 0) + away_stats.get('shots', 0)) / minute * 15
            features['momentum'] = (home_stats.get('shots', 0) - away_stats.get('shots', 0)) / minute * 15
        else:
            features['recent_intensity'] = 0
            features['momentum'] = 0
        
        # Ожидаемые голы до конца матча
        remaining = 90 - minute
        features['expected_goals_remaining'] = (home_stats.get('xg', 0.5) + away_stats.get('xg', 0.5)) * (remaining / 90)
        
        return features