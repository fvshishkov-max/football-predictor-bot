# advanced_features.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Генерация продвинутых признаков для прогнозирования голов
    Вдохновлено проектом futbol_corners_forecast
    """
    
    def __init__(self):
        self.feature_names = []
        
    def create_advanced_features(self, team_stats: Dict, opponent_stats: Dict, 
                                 h2h_data: List[Dict], league_avg: Dict) -> Dict:
        """
        Создает расширенный набор признаков
        
        Args:
            team_stats: Статистика команды
            opponent_stats: Статистика соперника
            h2h_data: История личных встреч
            league_avg: Средние показатели по лиге
            
        Returns:
            Dict с новыми признаками
        """
        features = {}
        
        # 1. Базовые признаки (9)
        features.update(self._create_basic_features(team_stats, league_avg))
        features.update(self._create_basic_features(opponent_stats, league_avg, prefix='opp_'))
        
        # 2. Продвинутые признаки (15)
        features.update(self._create_advanced_features(team_stats, prefix='team_'))
        features.update(self._create_advanced_features(opponent_stats, prefix='opp_'))
        
        # 3. Head-to-Head признаки
        features.update(self._create_h2h_features(h2h_data))
        
        # 4. Контекстные признаки
        features.update(self._create_context_features(team_stats, opponent_stats))
        
        # 5. Индексы эффективности
        features.update(self._create_efficiency_indices(team_stats, opponent_stats))
        
        self.feature_names = list(features.keys())
        return features
    
    def _create_basic_features(self, stats: Dict, league_avg: Dict, prefix: str = '') -> Dict:
        """Создает базовые признаки (9 штук)"""
        features = {}
        
        # Средние значения с нормализацией по лиге
        basic_stats = [
            ('shots', 'shots_avg'),
            ('shots_on_target', 'sot_avg'),
            ('xg', 'xg_avg'),
            ('corners', 'ck_avg'),
            ('possession', 'pos_avg'),
            ('dangerous_attacks', 'da_avg'),
            ('goals_for', 'gf_avg'),
            ('goals_against', 'ga_avg'),
            ('passes', 'pass_avg')
        ]
        
        for stat_key, feat_name in basic_stats:
            value = stats.get(stat_key, 0)
            league_value = league_avg.get(stat_key, 1)
            # Нормализованное значение (отклонение от среднего по лиге)
            features[f'{prefix}{feat_name}'] = value / league_value if league_value > 0 else 1.0
            # Вариация (коэффициент вариации за последние 5 матчей)
            features[f'{prefix}{feat_name}_var'] = self._calculate_variance(stats, stat_key)
        
        return features
    
    def _create_advanced_features(self, stats: Dict, prefix: str = '') -> Dict:
        """Создает продвинутые признаки (15 штук)"""
        features = {}
        
        # SHOTS
        shots = stats.get('shots', 0)
        sot = stats.get('shots_on_target', 0)
        xg = stats.get('xg', 0.5)
        
        features[f'{prefix}shot_accuracy'] = sot / shots if shots > 0 else 0
        features[f'{prefix}xg_per_shot'] = xg / shots if shots > 0 else 0.1
        features[f'{prefix}possession_shot'] = stats.get('possession', 50) * shots / 100
        
        # PASSES
        passes = stats.get('passes', 0)
        progressive_passes = stats.get('progressive_passes', passes * 0.2)  # Proxy
        final_third_passes = stats.get('final_third_passes', passes * 0.15)  # Proxy
        
        features[f'{prefix}progressive_pass_ratio'] = progressive_passes / passes if passes > 0 else 0.2
        features[f'{prefix}final_third_involvement'] = final_third_passes / passes if passes > 0 else 0.15
        features[f'{prefix}assist_sca'] = stats.get('assists', 0) / stats.get('sca', 1)  # Shot creating actions
        features[f'{prefix}creative_efficiency'] = stats.get('key_passes', 0) / passes if passes > 0 else 0
        
        # DEFENSE
        tackles = stats.get('tackles', 0)
        interceptions = stats.get('interceptions', 0)
        clearances = stats.get('clearances', 0)
        
        features[f'{prefix}interception_tackle'] = interceptions / tackles if tackles > 0 else 0
        features[f'{prefix}clearance_ratio'] = clearances / stats.get('shots_against', 1)
        features[f'{prefix}high_press_intensity'] = tackles / stats.get('opponent_passes', 100)
        
        # POSSESSION
        carries = stats.get('carries', passes * 0.5)  # Proxy
        progressive_carries = stats.get('progressive_carries', carries * 0.1)  # Proxy
        
        features[f'{prefix}progressive_carry_ratio'] = progressive_carries / carries if carries > 0 else 0.1
        features[f'{prefix}carry_pass_balance'] = carries / passes if passes > 0 else 0.5
        features[f'{prefix}transition_index'] = progressive_carries / stats.get('possession', 50)
        
        # ATTACK
        features[f'{prefix}offensive_index'] = (shots * 0.3 + xg * 0.5 + sot * 0.2) / 3
        features[f'{prefix}attacking_presence'] = (stats.get('touches_in_box', 0) + shots) / 2
        
        return features
    
    def _create_h2h_features(self, h2h_data: List[Dict]) -> Dict:
        """Создает признаки на основе истории встреч (48 вариантов)"""
        features = {}
        
        if not h2h_data:
            return features
        
        matches = len(h2h_data)
        
        # Средние значения за последние 3 встречи
        for i, match in enumerate(h2h_data[:3]):
            features[f'h2h_{i+1}_goals'] = match.get('goals_for', 0)
            features[f'h2h_{i+1}_xg'] = match.get('xg_for', 0)
            features[f'h2h_{i+1}_corners'] = match.get('corners', 0)
            features[f'h2h_{i+1}_shots'] = match.get('shots', 0)
            features[f'h2h_{i+1}_possession'] = match.get('possession', 50)
        
        # Агрегированные за все встречи
        features['h2h_avg_goals'] = np.mean([m.get('goals_for', 0) for m in h2h_data])
        features['h2h_avg_xg'] = np.mean([m.get('xg_for', 0) for m in h2h_data])
        features['h2h_avg_corners'] = np.mean([m.get('corners', 0) for m in h2h_data])
        features['h2h_win_rate'] = sum([1 for m in h2h_data if m.get('result') == 'win']) / matches
        
        return features
    
    def _create_context_features(self, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Создает контекстные признаки"""
        features = {}
        
        # Разница в показателях
        features['diff_xg'] = team_stats.get('xg', 0) - opponent_stats.get('xg', 0)
        features['diff_possession'] = team_stats.get('possession', 50) - opponent_stats.get('possession', 50)
        features['diff_shots'] = team_stats.get('shots', 0) - opponent_stats.get('shots', 0)
        
        # Соотношения
        features['shot_ratio'] = team_stats.get('shots', 0) / (opponent_stats.get('shots', 1) + 1)
        features['xg_ratio'] = team_stats.get('xg', 0.5) / (opponent_stats.get('xg', 0.5) + 0.1)
        
        return features
    
    def _create_efficiency_indices(self, team_stats: Dict, opponent_stats: Dict) -> Dict:
        """Создает индексы эффективности"""
        features = {}
        
        # Эффективность атаки
        shots = team_stats.get('shots', 0)
        goals = team_stats.get('goals_for', 0)
        features['attack_efficiency'] = goals / shots if shots > 0 else 0.1
        
        # Эффективность защиты
        shots_conceded = opponent_stats.get('shots', 0)
        goals_conceded = team_stats.get('goals_against', 0)
        features['defense_efficiency'] = 1 - (goals_conceded / shots_conceded if shots_conceded > 0 else 0.1)
        
        # Конверсия xG
        features['xg_conversion'] = goals / team_stats.get('xg', 0.5) if team_stats.get('xg', 0) > 0 else 0.5
        
        return features
    
    def _calculate_variance(self, stats: Dict, key: str) -> float:
        """Рассчитывает коэффициент вариации для показателя"""
        # В реальности нужно брать историю за последние N матчей
        # Здесь упрощенная версия
        values = stats.get(f'{key}_history', [stats.get(key, 0)] * 5)
        if len(values) < 2:
            return 0
        cv = np.std(values) / (np.mean(values) + 0.01)
        return min(cv, 1.0)  # Ограничиваем до 1


class ReliabilityScorer:
    """
    Оценка надежности прогноза на основе стабильности команд
    """
    
    def __init__(self):
        pass
    
    def calculate_score(self, team_stats: Dict, opponent_stats: Dict, 
                       predictions: Dict) -> Dict:
        """
        Рассчитывает оценку надежности прогноза
        
        Returns:
            Dict с оценкой и уровнем
        """
        # Стабильность команд (коэффициент вариации)
        team_cv = self._get_cv(team_stats)
        opp_cv = self._get_cv(opponent_stats)
        
        # Тренды
        team_trend = self._get_trend(team_stats)
        opp_trend = self._get_trend(opponent_stats)
        
        # Консистентность
        team_consistency = 1 - min(team_cv, 1)
        opp_consistency = 1 - min(opp_cv, 1)
        
        # Итоговая оценка
        score = (
            (team_consistency + opp_consistency) * 40 +
            (1 - abs(team_trend)) * 30 +
            (1 - abs(opp_trend)) * 30
        ) / 100
        
        # Определяем уровень
        if score > 0.7:
            level = "VERY_HIGH"
            stars = "⭐⭐⭐"
        elif score > 0.5:
            level = "HIGH"
            stars = "⭐⭐"
        elif score > 0.3:
            level = "MEDIUM"
            stars = "⭐"
        else:
            level = "LOW"
            stars = "⚠️"
        
        return {
            'score': round(score * 100),
            'level': level,
            'stars': stars,
            'team_stability': round(team_consistency * 100),
            'opponent_stability': round(opp_consistency * 100),
            'team_trend': round(team_trend * 100),
            'opponent_trend': round(opp_trend * 100)
        }
    
    def _get_cv(self, stats: Dict) -> float:
        """Коэффициент вариации"""
        # В реальности нужно брать исторические данные
        return stats.get('variance', 0.2)
    
    def _get_trend(self, stats: Dict) -> float:
        """Тренд формы (-1 до 1)"""
        return stats.get('trend', 0)