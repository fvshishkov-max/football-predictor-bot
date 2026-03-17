import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json
import os
import random
import traceback
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

from models import Match, LiveStats
from team_form import TeamFormAnalyzer
from statistical_models import StatisticalModels, MonteCarloSimulator, TimeSeriesAnalyzer
from club_elo_api import IntegratedEloPredictor

logger = logging.getLogger(__name__)

class Predictor:
    """
    Класс для прогнозирования голов в футбольных матчах на основе статистики.
    Использует расширенные статистические модели и машинное обучение.
    """
    
    def __init__(self, model_path: str = 'data/ml_model.pkl'):
        # Веса для различных факторов (будут обновляться регрессией)
        self.weights = {
            'xg': 0.28,
            'shots_ontarget': 0.18,
            'team_form': 0.15,
            'dangerous_attacks': 0.12,
            'shots': 0.10,
            'corners': 0.09,
            'possession': 0.05,
            'h2h': 0.03
        }
        
        self.weights_history = []
        
        # Пороговые значения
        self.thresholds = {
            'low': 0.15,
            'medium': 0.25,
            'high': 0.40,
            'very_high': 0.55
        }
        
        self.predictions_history = []
        self.max_history_size = 1000
        
        self.accuracy_stats = {
            'total_predictions': 0,
            'total_signals': 0,
            'correct_predictions': 0,
            'incorrect_predictions': 0,
            'accuracy_rate': 0.0,
            'goals_predicted': 0,
            'goals_actual': 0,
            'calibration_data': [],
            'feature_importance': {},
            'by_confidence': {
                'VERY_HIGH': {'total': 0, 'correct': 0},
                'HIGH': {'total': 0, 'correct': 0},
                'MEDIUM': {'total': 0, 'correct': 0},
                'LOW': {'total': 0, 'correct': 0},
                'VERY_LOW': {'total': 0, 'correct': 0}
            },
            'by_minute': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'by_league': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'regression_stats': {},
            'poisson_stats': {},
            'last_updated': datetime.now().isoformat()
        }
        
        self.team_analyzer = TeamFormAnalyzer()
        self.stat_models = StatisticalModels()
        self.monte_carlo = MonteCarloSimulator(n_simulations=10000)
        self.time_series = TimeSeriesAnalyzer()
        
        self.league_levels = self._init_league_levels()
        self.learning_rate = 0.01
        self.min_matches_for_update = 50
        self.model_path = model_path
        self.ml_model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'xg', 'shots_ontarget', 'team_form', 'dangerous_attacks',
            'shots', 'corners', 'possession', 'h2h', 'home_advantage',
            'league_level', 'minute_norm'
        ]
        self._init_ml_model()
        self._last_factors_contributions = {}
        
        # Для отслеживания голов по таймам
        self.half_goals = {}
        self.half_signals = {}
        
        # Для контроля дублирования сигналов
        self.match_last_signal = {}  # Время последнего сигнала для матча
        self.match_signal_count = {}  # Количество сигналов для матча
        self.max_signals_per_match = 3  # Максимум сигналов на матч
        self.min_time_between_signals = 600  # Минимум 10 минут между сигналами для одного матча
        
        # Инициализация Elo интеграции
        self.elo_predictor = None
        self.use_elo = True
        
        # Словарь синонимов для статистики
        self.stat_synonyms = {
            'shots': ['shots', 'totalShots', 'shotsTotal', 'attempts', 'total attempts'],
            'shots_on_target': ['shotsOnTarget', 'shotsOnGoal', 'onTarget', 'shots_ontarget'],
            'possession': ['possession', 'ballPossession', 'possessionPercentage'],
            'corners': ['corners', 'cornerKicks', 'cornersTotal'],
            'fouls': ['fouls', 'foulsCommitted'],
            'yellow_cards': ['yellowCards', 'yellow'],
            'red_cards': ['redCards', 'red'],
            'dangerous_attacks': ['dangerousAttacks', 'attacks'],
            'xg': ['xg', 'expectedGoals', 'xG']
        }
        
        logger.info("Predictor инициализирован с весами: %s", self.weights)
        logger.info(f"Пороги уверенности: {self.thresholds}")
    
    def _init_ml_model(self):
        """Инициализирует или загружает модель машинного обучения"""
        try:
            if os.path.exists(self.model_path):
                self.ml_model = joblib.load(self.model_path)
                logger.info(f"✅ Загружена ML модель из {self.model_path}")
            else:
                self.ml_model = LogisticRegression(
                    max_iter=1000,
                    class_weight='balanced',
                    random_state=42
                )
                logger.info("✅ Создана новая ML модель")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ML модели: {e}")
            self.ml_model = LogisticRegression(
                max_iter=1000,
                class_weight='balanced',
                random_state=42
            )
    
    def _init_league_levels(self) -> Dict:
        """Инициализирует уровни лиг"""
        top_leagues = {
            1: 1, 2: 1, 3: 1, 4: 1, 5: 1,
            6: 2, 7: 2, 8: 2, 9: 2, 10: 2,
        }
        return defaultdict(lambda: 2, top_leagues)
    
    def _get_stat_value(self, stats_dict: Dict, stat_name: str, default: Any = 0) -> Any:
        """Получает значение статистики по синонимам"""
        if stat_name not in self.stat_synonyms:
            return stats_dict.get(stat_name, default)
        
        for synonym in self.stat_synonyms[stat_name]:
            if synonym in stats_dict:
                return stats_dict[synonym]
            
            synonym_lower = synonym.lower()
            for key, value in stats_dict.items():
                if key.lower() == synonym_lower:
                    return value
                
            if isinstance(stats_dict, dict):
                for key, value in stats_dict.items():
                    if isinstance(value, dict):
                        result = self._get_stat_value(value, stat_name, None)
                        if result is not None:
                            return result
        
        return default
    
    def _ensure_dict(self, data: Any, name: str = "data") -> Dict:
        """Гарантированно преобразует данные в словарь"""
        if data is None:
            logger.debug(f"{name} is None, возвращаем пустой словарь")
            return {}
        
        if isinstance(data, dict):
            return data
        
        if hasattr(data, '__dict__'):
            logger.debug(f"{name} является объектом, конвертируем в dict")
            return data.__dict__
        
        if isinstance(data, (list, tuple, set)):
            logger.debug(f"{name} является {type(data)}, конвертируем в dict")
            return {str(i): v for i, v in enumerate(data)}
        
        logger.debug(f"{name} имеет неожиданный тип {type(data)}, возвращаем пустой словарь")
        return {}
    
    def _generate_match_url(self, match: Match) -> str:
        """Генерирует ссылку на Sofascore с правильной обработкой спецсимволов"""
        if not match.home_team or not match.away_team:
            return "https://www.sofascore.com"
        
        def create_slug(name: str) -> str:
            # Транслитерация для кириллицы
            translit = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
                'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
                'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
                'А': 'a', 'Б': 'b', 'В': 'v', 'Г': 'g', 'Д': 'd', 'Е': 'e', 'Ё': 'e',
                'Ж': 'zh', 'З': 'z', 'И': 'i', 'Й': 'y', 'К': 'k', 'Л': 'l', 'М': 'm',
                'Н': 'n', 'О': 'o', 'П': 'p', 'Р': 'r', 'С': 's', 'Т': 't', 'У': 'u',
                'Ф': 'f', 'Х': 'kh', 'Ц': 'ts', 'Ч': 'ch', 'Ш': 'sh', 'Щ': 'shch',
                'Ъ': '', 'Ы': 'y', 'Ь': '', 'Э': 'e', 'Ю': 'yu', 'Я': 'ya'
            }
            
            result = ''
            for char in name:
                if char in translit:
                    result += translit[char]
                elif char.isalnum() or char == ' ':
                    result += char
                else:
                    # Заменяем специальные символы
                    if char in ['º', '°', 'ó', 'ò', 'ô', 'ö']:
                        result += 'o'
                    elif char in ['á', 'à', 'â', 'ä', 'ã']:
                        result += 'a'
                    elif char in ['é', 'è', 'ê', 'ë']:
                        result += 'e'
                    elif char in ['í', 'ì', 'î', 'ï']:
                        result += 'i'
                    elif char in ['ú', 'ù', 'û', 'ü']:
                        result += 'u'
                    elif char == 'ñ':
                        result += 'n'
                    elif char == 'ç':
                        result += 'c'
                    elif char == '®':
                        result += 'r'
                    elif char == '©':
                        result += 'c'
                    elif char == 'ß':
                        result += 'ss'
                    elif char == 'æ':
                        result += 'ae'
                    else:
                        result += ''
            
            result = result.lower()
            result = result.replace(' ', '-')
            result = result.replace('.', '')
            result = result.replace('&', 'and')
            result = result.replace('+', 'plus')
            result = result.replace('fc', '')
            result = result.replace('cf', '')
            result = result.replace('--', '-')
            result = result.strip('-')
            
            while '--' in result:
                result = result.replace('--', '-')
            
            result = result.strip('-')
            return result if result else "match"
        
        home_slug = create_slug(match.home_team.name)
        away_slug = create_slug(match.away_team.name)
        
        return f"https://www.sofascore.com/ru/football/match/{home_slug}-vs-{away_slug}/{match.id}"
    
    def _should_analyze_match(self, match: Match) -> bool:
        """Проверяет, стоит ли анализировать матч"""
        if match.minute and match.minute > 75:
            logger.debug(f"Пропускаем матч {match.id}: время {match.minute}' > 75'")
            return False
        
        home_score = match.home_score or 0
        away_score = match.away_score or 0
        score_diff = abs(home_score - away_score)
        
        if score_diff >= 3:
            logger.debug(f"Пропускаем матч {match.id}: крупный счет {home_score}:{away_score}")
            return False
        
        if home_score >= 4 or away_score >= 4:
            logger.debug(f"Пропускаем матч {match.id}: много голов {home_score}:{away_score}")
            return False
        
        return True
    
    def calculate_total_probabilities(self, home_lambda: float, away_lambda: float) -> Dict:
        """
        Рассчитывает вероятности для различных тоталов используя распределение Пуассона
        
        Args:
            home_lambda: Интенсивность голов хозяев
            away_lambda: Интенсивность голов гостей
            
        Returns:
            Dict с вероятностями для разных тоталов
        """
        max_goals = 10
        total_probs = {}
        
        # Рассчитываем распределение для общего количества голов
        for total in range(max_goals * 2 + 1):
            prob = 0
            for i in range(max_goals + 1):
                for j in range(max_goals + 1):
                    if i + j == total:
                        prob += self.stat_models.poisson_probability(home_lambda, i) * \
                                self.stat_models.poisson_probability(away_lambda, j)
            total_probs[total] = prob
        
        # Рассчитываем вероятности для различных тоталов
        results = {
            'under_0.5': total_probs.get(0, 0),
            'over_0.5': 1 - total_probs.get(0, 0),
            'under_1.5': sum(total_probs.get(i, 0) for i in range(2)),
            'over_1.5': 1 - sum(total_probs.get(i, 0) for i in range(2)),
            'under_2.5': sum(total_probs.get(i, 0) for i in range(3)),
            'over_2.5': 1 - sum(total_probs.get(i, 0) for i in range(3)),
            'under_3.5': sum(total_probs.get(i, 0) for i in range(4)),
            'over_3.5': 1 - sum(total_probs.get(i, 0) for i in range(4)),
            'under_4.5': sum(total_probs.get(i, 0) for i in range(5)),
            'over_4.5': 1 - sum(total_probs.get(i, 0) for i in range(5)),
            'exact_0': total_probs.get(0, 0),
            'exact_1': total_probs.get(1, 0),
            'exact_2': total_probs.get(2, 0),
            'exact_3': total_probs.get(3, 0),
            'exact_4': total_probs.get(4, 0),
        }
        
        return results
    
    def calculate_best_bet(self, home_prob: float, away_prob: float, total_prob: float, match: Optional[Match] = None) -> Dict:
        """
        Определяет наилучший вариант ставки на основе вероятностей
        
        Args:
            home_prob: Вероятность гола хозяев
            away_prob: Вероятность гола гостей
            total_prob: Общая вероятность гола
            match: Объект матча (для H2H)
            
        Returns:
            Dict с рекомендациями по ставкам
        """
        home_lambda = home_prob * 3
        away_lambda = away_prob * 3
        
        total_probs = self.calculate_total_probabilities(home_lambda, away_lambda)
        
        # Находим наиболее вероятные исходы
        recommendations = []
        
        # Тоталы
        for total_type in ['over_0.5', 'over_1.5', 'over_2.5', 'over_3.5', 'under_2.5']:
            prob = total_probs.get(total_type, 0)
            if prob > 0.55:  # 55% вероятность
                confidence = 'HIGH' if prob > 0.65 else 'MEDIUM'
                confidence = 'VERY_HIGH' if prob > 0.75 else confidence
                
                # Человеко-читаемое название
                display_name = {
                    'over_0.5': 'Тотал больше 0.5',
                    'over_1.5': 'Тотал больше 1.5',
                    'over_2.5': 'Тотал больше 2.5',
                    'over_3.5': 'Тотал больше 3.5',
                    'under_2.5': 'Тотал меньше 2.5'
                }.get(total_type, total_type)
                
                recommendations.append({
                    'type': 'total',
                    'market': display_name,
                    'probability': round(prob * 100, 1),
                    'confidence': confidence
                })
        
        # Точный счет (только если вероятность > 10%)
        for score in ['exact_0', 'exact_1', 'exact_2', 'exact_3']:
            prob = total_probs.get(score, 0)
            if prob > 0.10:
                goals = score.split('_')[1]
                confidence = 'MEDIUM' if prob > 0.15 else 'LOW'
                
                recommendations.append({
                    'type': 'exact_score',
                    'market': f'Точный счет {goals}:{goals}',
                    'probability': round(prob * 100, 1),
                    'confidence': confidence
                })
        
        # Победитель (если есть данные о матче)
        if match and hasattr(self, '_get_h2h_factor'):
            try:
                h2h_factors = self._get_h2h_factor(match)
                
                # Простая оценка вероятности победы
                home_win_prob = home_prob / (home_prob + away_prob) * 0.7 + 0.15
                away_win_prob = away_prob / (home_prob + away_prob) * 0.7 + 0.15
                draw_prob = 1 - home_win_prob - away_win_prob
                
                # Корректировка на H2H
                home_win_prob *= h2h_factors.get('home', 1.0)
                away_win_prob *= h2h_factors.get('away', 1.0)
                
                # Нормализация
                total = home_win_prob + away_win_prob + draw_prob
                if total > 0:
                    home_win_prob /= total
                    away_win_prob /= total
                    draw_prob /= total
                
                if home_win_prob > 0.40:
                    confidence = 'HIGH' if home_win_prob > 0.55 else 'MEDIUM'
                    recommendations.append({
                        'type': 'winner',
                        'market': 'Победа хозяев',
                        'probability': round(home_win_prob * 100, 1),
                        'confidence': confidence
                    })
                elif away_win_prob > 0.40:
                    confidence = 'HIGH' if away_win_prob > 0.55 else 'MEDIUM'
                    recommendations.append({
                        'type': 'winner',
                        'market': 'Победа гостей',
                        'probability': round(away_win_prob * 100, 1),
                        'confidence': confidence
                    })
                
                if draw_prob > 0.30:
                    recommendations.append({
                        'type': 'draw',
                        'market': 'Ничья',
                        'probability': round(draw_prob * 100, 1),
                        'confidence': 'MEDIUM' if draw_prob > 0.35 else 'LOW'
                    })
            except Exception as e:
                logger.debug(f"Ошибка расчета H2H фактора: {e}")
        
        # Обе забьют
        try:
            both_score_prob = 1 - (total_probs.get('exact_0', 0) + 
                                   (self.stat_models.poisson_probability(home_lambda, 0) * 
                                    self.stat_models.poisson_probability(away_lambda, 1)) +
                                   (self.stat_models.poisson_probability(home_lambda, 1) * 
                                    self.stat_models.poisson_probability(away_lambda, 0)))
            
            if both_score_prob > 0.45:
                confidence = 'HIGH' if both_score_prob > 0.60 else 'MEDIUM'
                confidence = 'VERY_HIGH' if both_score_prob > 0.70 else confidence
                
                recommendations.append({
                    'type': 'both_score',
                    'market': 'Обе забьют (ДА)',
                    'probability': round(both_score_prob * 100, 1),
                    'confidence': confidence
                })
        except Exception as e:
            logger.debug(f"Ошибка расчета обе забьют: {e}")
        
        # Сортируем по вероятности
        recommendations = sorted(recommendations, key=lambda x: x['probability'], reverse=True)
        
        return {
            'total_probabilities': total_probs,
            'recommendations': recommendations[:5]  # Топ-5 рекомендаций
        }
    
    def predict_match(self, match: Match) -> Dict:
        """Предсказание с использованием всех статистических моделей"""
        try:
            # Получаем статистику и гарантируем, что это словари
            home_stats_raw = self._extract_team_stats(match, is_home=True)
            away_stats_raw = self._extract_team_stats(match, is_home=False)
            
            # Принудительно преобразуем в словари
            home_stats = self._ensure_dict(home_stats_raw, "home_stats")
            away_stats = self._ensure_dict(away_stats_raw, "away_stats")
            
            logger.debug(f"home_stats тип: {type(home_stats)}, содержимое: {list(home_stats.keys()) if isinstance(home_stats, dict) else 'не словарь'}")
            
            home_form = None
            away_form = None
            
            if match.home_team and hasattr(match.home_team, 'id') and match.home_team.id:
                home_form = self.team_analyzer.get_team_form(match.home_team.id)
                
            if match.away_team and hasattr(match.away_team, 'id') and match.away_team.id:
                away_form = self.team_analyzer.get_team_form(match.away_team.id)
            
            h2h_factors = self._get_h2h_factor(match)
            league_factor = self._get_league_factor(match)
            
            home_vs_top = self._get_performance_vs_top(match.home_team.id) if match.home_team else 1.0
            away_vs_top = self._get_performance_vs_top(match.away_team.id) if match.away_team else 1.0
            
            # Базовые вероятности
            home_goal_prob = self._calculate_goal_probability(
                home_stats, is_home=True, team_form=home_form,
                h2h_factor=h2h_factors['home'] if h2h_factors else 1.0,
                league_factor=league_factor,
                top_teams_factor=home_vs_top
            )
            
            away_goal_prob = self._calculate_goal_probability(
                away_stats, is_home=False, team_form=away_form,
                h2h_factor=h2h_factors['away'] if h2h_factors else 1.0,
                league_factor=league_factor,
                top_teams_factor=away_vs_top
            )
            
            # Пуассон-модель для точных счетов
            home_lambda = home_goal_prob * 3  # Конвертация в интенсивность
            away_lambda = away_goal_prob * 3
            poisson_probs = self.stat_models.match_goal_probabilities(
                home_lambda, away_lambda
            )
            
            # Монте-Карло симуляция
            mc_results = self.monte_carlo.simulate_match(
                home_goal_prob * 3,
                away_goal_prob * 3
            )
            
            # Расчет рекомендаций по ставкам
            betting_recommendations = self.calculate_best_bet(
                home_goal_prob, away_goal_prob, 
                home_goal_prob + away_goal_prob, 
                match
            )
            
            home_goal_prob = self._calibrate_probability(home_goal_prob)
            away_goal_prob = self._calibrate_probability(away_goal_prob)
            total_goal_prob = self._calculate_total_goal_probability(home_goal_prob, away_goal_prob)
            confidence_level = self._determine_confidence_level(total_goal_prob)
            
            match_url = self._generate_match_url(match)
            
            signal = self._generate_signal(
                match, home_goal_prob, away_goal_prob, total_goal_prob, 
                confidence_level, home_stats, away_stats, home_form, away_form, match_url,
                poisson_probs, mc_results, betting_recommendations
            )
            
            result = {
                'match_id': match.id,
                'match': match,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'league_name': match.league_name,
                'country_code': match.home_team.country_code if match.home_team else None,
                'home_goal_probability': round(home_goal_prob, 3),
                'away_goal_probability': round(away_goal_prob, 3),
                'total_goal_probability': round(total_goal_prob, 3),
                'confidence_level': confidence_level,
                'signal': signal,
                'home_stats': home_stats,
                'away_stats': away_stats,
                'home_form': home_form,
                'away_form': away_form,
                'h2h_factors': h2h_factors,
                'match_url': match_url,
                'league_id': match.league_id,
                'minute': match.minute,
                'poisson_probs': poisson_probs,
                'monte_carlo': mc_results,
                'betting_recommendations': betting_recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            self._add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при предсказании матча {match.id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._get_default_prediction(match)
    
    async def predict_match_with_elo(self, match: Match) -> Dict:
        """
        Предсказание с интеграцией Elo рейтингов
        """
        try:
            # Получаем базовое предсказание
            base_prediction = self.predict_match(match)
            
            # Если есть ошибка, возвращаем базовое
            if base_prediction.get('error', False):
                return base_prediction
            
            # Инициализируем Elo при первом использовании
            if self.use_elo and not self.elo_predictor:
                try:
                    self.elo_predictor = IntegratedEloPredictor(self)
                    logger.info("✅ Elo интеграция инициализирована")
                except Exception as e:
                    logger.error(f"❌ Ошибка инициализации Elo: {e}")
                    self.use_elo = False
                    return base_prediction
            
            # Улучшаем предсказание с помощью Elo
            if self.use_elo and self.elo_predictor:
                enhanced = await self.elo_predictor.enhance_prediction(match, base_prediction)
                
                # Добавляем Elo данные в сигнал для отображения
                if enhanced.get('elo_data'):
                    base_prediction['elo_data'] = enhanced['elo_data']
                    base_prediction['home_goal_probability'] = enhanced['home_goal_probability']
                    base_prediction['away_goal_probability'] = enhanced['away_goal_probability']
                    base_prediction['total_goal_probability'] = enhanced['total_goal_probability']
                    
                    # Пересчитываем уровень уверенности
                    base_prediction['confidence_level'] = self._determine_confidence_level(
                        base_prediction['total_goal_probability']
                    )
            
            return base_prediction
            
        except Exception as e:
            logger.error(f"Ошибка Elo предсказания: {e}")
            return self.predict_match(match)  # Fallback к обычному методу
    
    def _get_h2h_factor(self, match: Match) -> Dict:
        """Анализирует историю личных встреч"""
        if not match.home_team or not match.away_team:
            return {'home': 1.0, 'away': 1.0}
        
        try:
            h2h_data = self.team_analyzer.get_head_to_head(
                match.home_team.id,
                match.away_team.id,
                limit=5
            )
            
            if h2h_data['matches_played'] == 0:
                return {'home': 1.0, 'away': 1.0}
            
            home_factor = 1.0
            away_factor = 1.0
            
            home_advantage = (h2h_data['team1_wins'] - h2h_data['team2_wins']) / h2h_data['matches_played']
            
            if h2h_data['team1_avg_goals'] > h2h_data['team2_avg_goals']:
                home_factor *= (1 + (h2h_data['team1_avg_goals'] - h2h_data['team2_avg_goals']) * 0.1)
            else:
                away_factor *= (1 + (h2h_data['team2_avg_goals'] - h2h_data['team1_avg_goals']) * 0.1)
            
            if h2h_data.get('trend', 0) > 0:
                home_factor *= 1.1
            elif h2h_data.get('trend', 0) < 0:
                away_factor *= 1.1
            
            if h2h_data.get('last_result') == 'team1_win':
                home_factor *= 1.15
            elif h2h_data.get('last_result') == 'team2_win':
                away_factor *= 1.15
            
            home_factor = max(0.8, min(1.2, home_factor))
            away_factor = max(0.8, min(1.2, away_factor))
            
            return {'home': home_factor, 'away': away_factor}
        except Exception as e:
            logger.debug(f"Ошибка получения H2H данных: {e}")
            return {'home': 1.0, 'away': 1.0}
    
    def _get_league_factor(self, match: Match) -> float:
        """Фактор силы лиги"""
        if not match.league_id:
            return 1.0
        
        level = self.league_levels.get(match.league_id, 2)
        
        if level == 1:
            return 1.1
        else:
            return 0.95
    
    def _get_performance_vs_top(self, team_id: int) -> float:
        """Анализ против топ-команд"""
        try:
            stats = self.team_analyzer.get_team_performance_vs_top_teams(team_id)
            
            if stats['matches_analyzed'] == 0:
                return 1.0
            
            if stats['points_per_game'] > 1.5:
                return 1.15
            elif stats['points_per_game'] < 0.8:
                return 0.85
            else:
                return 1.0
        except Exception as e:
            logger.debug(f"Ошибка получения performance vs top: {e}")
            return 1.0
    
    def _calculate_goal_probability(self, stats: Dict, is_home: bool = True, 
                                   team_form: Optional[Dict] = None,
                                   h2h_factor: float = 1.0,
                                   league_factor: float = 1.0,
                                   top_teams_factor: float = 1.0) -> float:
        """Вероятность гола с учетом статистики"""
        factors = []
        total_weight = 0
        
        # Убеждаемся, что stats - словарь
        if not isinstance(stats, dict):
            logger.warning(f"stats не является словарем: {type(stats)}, используем пустой словарь")
            stats = {}
        
        # Проверяем, есть ли реальная статистика
        has_real_stats = any([
            stats.get('shots', 0) > 0,
            stats.get('shots_on_target', 0) > 0,
            stats.get('dangerous_attacks', 0) > 0
        ])
        
        if not has_real_stats:
            base_prob = 0.25 + (0.05 if is_home else 0)
            
            if team_form and isinstance(team_form, dict):
                form_factor = team_form.get('weighted_form', team_form.get('form', 0.5))
                base_prob += (form_factor - 0.5) * 0.15
            
            base_prob *= h2h_factor
            base_prob *= league_factor
            base_prob *= top_teams_factor
            
            variation = random.uniform(0.85, 1.15)
            base_prob *= variation
            
            return max(0.1, min(0.6, base_prob))
        
        # Нормализация значений с учетом реальной статистики
        factor_mappings = [
            ('xg', stats.get('xg', 0.5), 3.0, 0.3),
            ('shots_ontarget', stats.get('shots_on_target', 0), 15.0, 0.2),
            ('dangerous_attacks', stats.get('dangerous_attacks', 0), 70.0, 0.15),
            ('shots', stats.get('shots', 0), 30.0, 0.1),
            ('corners', stats.get('corners', 0), 15.0, 0.08),
            ('possession', stats.get('possession', 50), 100.0, 0.05)
        ]
        
        for key, value, max_val, base_weight in factor_mappings:
            if key in self.weights:
                weight = self.weights[key]
                normalized = min(value / max_val, 1.0)
                factors.append(normalized * weight)
                total_weight += weight
        
        if team_form and 'team_form' in self.weights and isinstance(team_form, dict):
            form_factor = team_form.get('weighted_form', team_form.get('form', 0.5))
            factors.append(form_factor * self.weights['team_form'])
            total_weight += self.weights['team_form']
        
        if 'h2h' in self.weights:
            factors.append(h2h_factor * self.weights['h2h'])
            total_weight += self.weights['h2h']
        
        if is_home:
            home_bonus = 0.05
            factors.append(home_bonus)
            total_weight += 0.05
        
        if total_weight > 0:
            probability = sum(factors) / total_weight
        else:
            probability = 0.3
        
        probability *= league_factor
        probability *= top_teams_factor
        
        variation = random.uniform(0.9, 1.1)
        probability *= variation
        
        return max(0.1, min(0.8, probability))
    
    def _calibrate_probability(self, probability: float) -> float:
        """Калибровка вероятности"""
        if len(self.accuracy_stats['calibration_data']) < 100:
            return probability
        
        calibration_data = self.accuracy_stats['calibration_data'][-100:]
        bins = np.linspace(0, 1, 11)
        bin_means = []
        
        for i in range(len(bins) - 1):
            bin_low = bins[i]
            bin_high = bins[i + 1]
            
            bin_probs = [p for p, actual in calibration_data 
                        if bin_low <= p < bin_high]
            bin_actuals = [actual for p, actual in calibration_data 
                          if bin_low <= p < bin_high]
            
            if len(bin_probs) > 0:
                mean_pred = np.mean(bin_probs)
                mean_actual = np.mean(bin_actuals)
                bin_means.append((mean_pred, mean_actual))
        
        for mean_pred, mean_actual in bin_means:
            if abs(probability - mean_pred) < 0.05:
                return mean_actual
        
        return probability
    
    def _calculate_total_goal_probability(self, home_prob: float, away_prob: float) -> float:
        """Общая вероятность гола"""
        total_prob = 1 - (1 - home_prob) * (1 - away_prob)
        
        if total_prob > 0.95:
            total_prob = 0.95
        elif total_prob < 0.3:
            total_prob = total_prob * 1.2
        
        return total_prob
    
    def _determine_confidence_level(self, probability: float) -> str:
        """Уровень уверенности"""
        if probability >= self.thresholds['very_high']:
            base_level = "VERY_HIGH"
        elif probability >= self.thresholds['high']:
            base_level = "HIGH"
        elif probability >= self.thresholds['medium']:
            base_level = "MEDIUM"
        elif probability >= self.thresholds['low']:
            base_level = "LOW"
        else:
            base_level = "VERY_LOW"
        
        if len(self.accuracy_stats['calibration_data']) > 50:
            level_stats = self.accuracy_stats['by_confidence'].get(base_level, {'total': 0, 'correct': 0})
            if level_stats['total'] > 5:
                historical_accuracy = level_stats['correct'] / level_stats['total'] if level_stats['total'] > 0 else 0
                
                if historical_accuracy > 0.6 and base_level in ["MEDIUM", "LOW"]:
                    if base_level == "MEDIUM":
                        return "HIGH"
                    elif base_level == "LOW":
                        return "MEDIUM"
                
                elif historical_accuracy < 0.3 and base_level in ["VERY_HIGH", "HIGH"]:
                    if base_level == "VERY_HIGH":
                        return "HIGH"
                    elif base_level == "HIGH":
                        return "MEDIUM"
        
        return base_level
    
    def _generate_signal(self, match: Match, home_prob: float, away_prob: float, 
                        total_prob: float, confidence: str, home_stats: Dict,
                        away_stats: Dict, home_form: Optional[Dict], 
                        away_form: Optional[Dict], match_url: str,
                        poisson_probs: Dict, mc_results: Dict,
                        betting_recommendations: Dict) -> Dict:
        """Генерация сигнала с расширенной статистикой и рекомендациями по тоталам"""
        confidence_emojis = {
            "VERY_HIGH": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "VERY_LOW": "⚪"
        }
        
        emoji = confidence_emojis.get(confidence, "⚪")
        
        home_name = match.home_team.name if match.home_team else "Home"
        away_name = match.away_team.name if match.away_team else "Away"
        
        # Информация о лиге и стране
        league_info = ""
        if match.league_name:
            league_info = f" ({match.league_name}"
            if match.home_team and match.home_team.country_code:
                league_info += f", {match.home_team.country_code}"
            league_info += ")"
        
        current_score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        period = ""
        if match.minute:
            if match.minute < 45:
                period = "1-й тайм"
            elif match.minute < 90:
                period = "2-й тайм"
            else:
                period = "Доп. время"
        
        # Убеждаемся, что home_stats и away_stats - словари
        if not isinstance(home_stats, dict):
            logger.warning(f"home_stats не словарь: {type(home_stats)}")
            home_stats = self._ensure_dict(home_stats, "home_stats")
        
        if not isinstance(away_stats, dict):
            logger.warning(f"away_stats не словарь: {type(away_stats)}")
            away_stats = self._ensure_dict(away_stats, "away_stats")
        
        has_stats = any([
            home_stats.get('shots', 0) > 0,
            away_stats.get('shots', 0) > 0,
            home_stats.get('shots_on_target', 0) > 0,
            away_stats.get('shots_on_target', 0) > 0,
            home_stats.get('corners', 0) > 0,
            away_stats.get('corners', 0) > 0
        ])
        
        message_lines = [
            f"{emoji} **Потенциальный гол!**",
            f"⚔️ **{home_name} vs {away_name}**{league_info}",
            f"📊 **Счет:** {current_score}",
            f"⏱️ **Минута:** {match.minute or 0}' {period}",
            "",
            f"📈 **Вероятность гола:** {total_prob*100:.1f}%",
            f"🎯 **Уверенность:** {confidence}",
            "",
            f"🏠 **{home_name}:** {home_prob*100:.1f}%",
            f"✈️ **{away_name}:** {away_prob*100:.1f}%",
        ]
        
        if has_stats:
            message_lines.extend([
                "",
                "📊 **СТАТИСТИКА МАТЧА:**",
                f"  • Удары: {home_stats.get('shots', 0)} : {away_stats.get('shots', 0)}",
                f"  • В створ: {home_stats.get('shots_on_target', 0)} : {away_stats.get('shots_on_target', 0)}",
                f"  • xG: {home_stats.get('xg', 0):.2f} : {away_stats.get('xg', 0):.2f}",
                f"  • Угловые: {home_stats.get('corners', 0)} : {away_stats.get('corners', 0)}",
                f"  • Владение: {home_stats.get('possession', 50)}% : {away_stats.get('possession', 50)}%",
                f"  • Опасные атаки: {home_stats.get('dangerous_attacks', 0)} : {away_stats.get('dangerous_attacks', 0)}",
            ])
        else:
            message_lines.extend([
                "",
                "📊 **СТАТИСТИКА МАТЧА:**",
                "  • Статистика временно недоступна"
            ])
        
        # Добавляем рекомендации по ставкам
        if betting_recommendations and betting_recommendations.get('recommendations'):
            message_lines.extend([
                "",
                "💰 **РЕКОМЕНДАЦИИ ПО СТАВКАМ:**"
            ])
            
            for rec in betting_recommendations['recommendations'][:3]:  # Топ-3
                rec_emoji = {
                    'VERY_HIGH': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(rec['confidence'], '⚪')
                
                message_lines.append(
                    f"  {rec_emoji} {rec['market']}: {rec['probability']}% ({rec['confidence']})"
                )
        
        # Добавляем форму команд
        if home_form or away_form:
            message_lines.extend([
                "",
                "📈 **ФОРМА КОМАНД (последние 5 матчей):**",
            ])
            
            if home_form and isinstance(home_form, dict):
                form_string = home_form.get('form_string', '')
                points = home_form.get('points_per_game', 0) * 5
                if form_string:
                    message_lines.append(f"  • {home_name}: {form_string} ({points:.0f} очков)")
                else:
                    message_lines.append(f"  • {home_name}: нет данных")
            
            if away_form and isinstance(away_form, dict):
                form_string = away_form.get('form_string', '')
                points = away_form.get('points_per_game', 0) * 5
                if form_string:
                    message_lines.append(f"  • {away_name}: {form_string} ({points:.0f} очков)")
                else:
                    message_lines.append(f"  • {away_name}: нет данных")
        
        # Добавляем информацию о голах в таймах
        match_id = match.id
        if match_id in self.half_goals:
            first_half = self.half_goals[match_id].get('first', 0)
            second_half = self.half_goals[match_id].get('second', 0)
            if first_half > 0 or second_half > 0:
                message_lines.extend([
                    "",
                    f"⚽️ **ГОЛЫ ПО ТАЙМАМ:**",
                    f"  • 1-й тайм: {first_half}",
                    f"  • 2-й тайм: {second_half}"
                ])
        
        message_lines.extend([
            "",
            f"🔗 **Смотреть матч:** {match_url}"
        ])
        
        message = "\n".join(message_lines)
        
        signal = {
            'emoji': emoji,
            'message': message,
            'confidence': confidence,
            'probability': total_prob,
            'home_prob': home_prob,
            'away_prob': away_prob,
            'match_id': match.id,
            'current_score': current_score,
            'match_url': match_url,
            'stats': {
                'home': home_stats,
                'away': away_stats
            },
            'form': {
                'home': home_form,
                'away': away_form
            },
            'poisson': poisson_probs,
            'monte_carlo': mc_results,
            'betting': betting_recommendations,
            'league_name': match.league_name,
            'country_code': match.home_team.country_code if match.home_team else None,
            'timestamp': datetime.now()
        }
        
        return signal
    
    def analyze_live_match(self, match: Match) -> Optional[Dict]:
        """Анализирует live-матч и генерирует сигнал с учетом таймов и дублирования"""
        try:
            # Проверяем, не слишком ли много сигналов для этого матча
            if match.id in self.match_signal_count:
                if self.match_signal_count[match.id] >= self.max_signals_per_match:
                    logger.debug(f"Пропускаем матч {match.id}: уже отправлено {self.match_signal_count[match.id]} сигналов")
                    return None
            
            # Проверяем, не отправляли ли сигнал недавно для этого матча
            if match.id in self.match_last_signal:
                time_since_last = (datetime.now() - self.match_last_signal[match.id]).total_seconds()
                if time_since_last < self.min_time_between_signals:
                    logger.debug(f"Пропускаем матч {match.id}: прошло только {time_since_last:.0f}с с последнего сигнала")
                    return None
            
            # Проверяем, стоит ли анализировать этот матч
            if not self._should_analyze_match(match):
                return None
            
            # Проверяем, не было ли уже голов в этом тайме
            if self._should_skip_half(match):
                logger.debug(f"Пропускаем матч {match.id}: уже были голы в этом тайме")
                return None
            
            prediction = self.predict_match(match)
            
            if self._should_send_signal(prediction):
                # Определяем тайм
                half = "1-й тайм" if match.minute and match.minute < 45 else "2-й тайм"
                
                # Обновляем информацию о сигнале
                self.match_last_signal[match.id] = datetime.now()
                self.match_signal_count[match.id] = self.match_signal_count.get(match.id, 0) + 1
                
                logger.info(f"📢 Сгенерирован сигнал для матча {match.id} ({half}) с вероятностью {prediction['total_goal_probability']:.2f} (всего сигналов: {self.match_signal_count[match.id]})")
                
                # Сохраняем информацию о сигнале для этого тайма
                self._save_signal_for_half(match, half)
                
                if match.is_finished and hasattr(self, 'team_analyzer'):
                    try:
                        if match.home_team and match.away_team and match.home_team.id and match.away_team.id:
                            home_xg = prediction.get('home_stats', {}).get('xg', 0)
                            away_xg = prediction.get('away_stats', {}).get('xg', 0)
                            
                            self.team_analyzer.save_match(
                                match_id=match.id,
                                home_id=match.home_team.id,
                                away_id=match.away_team.id,
                                home_score=match.home_score or 0,
                                away_score=match.away_score or 0,
                                match_date=match.start_time or datetime.now(),
                                league_id=match.league_id,
                                home_xg=home_xg,
                                away_xg=away_xg,
                                league_level=self.league_levels.get(match.league_id, 2)
                            )
                            
                            total_goals = (match.home_score or 0) + (match.away_score or 0)
                            self.update_accuracy(str(match.id), total_goals)
                            
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения матча {match.id} в историю: {e}")
                
                return prediction.get('signal')
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе live-матча {match.id}: {e}")
            return None
    
    def _should_skip_half(self, match: Match) -> bool:
        """Проверяет, нужно ли пропустить этот тайм (уже были голы)"""
        match_id = match.id
        current_half = "first" if match.minute and match.minute < 45 else "second"
        
        # Получаем голы в этом тайме
        if match_id not in self.half_goals:
            self.half_goals[match_id] = {'first': 0, 'second': 0}
        
        # Проверяем, были ли уже голы в этом тайме
        if current_half == "first":
            return self.half_goals[match_id]['first'] > 0
        else:
            return self.half_goals[match_id]['second'] > 0
    
    def _save_signal_for_half(self, match: Match, half: str):
        """Сохраняет информацию о сигнале для тайма"""
        match_id = match.id
        if match_id not in self.half_signals:
            self.half_signals[match_id] = []
        
        self.half_signals[match_id].append({
            'half': half,
            'minute': match.minute,
            'probability': match.total_goal_probability if hasattr(match, 'total_goal_probability') else 0,
            'timestamp': datetime.now()
        })
    
    def check_goal_scored(self, match: Match):
        """Проверяет, был ли забит гол, и обновляет статистику тайма"""
        match_id = match.id
        if match_id not in self.half_goals:
            self.half_goals[match_id] = {'first': 0, 'second': 0}
        
        current_half = "first" if match.minute and match.minute < 45 else "second"
        
        self.half_goals[match_id][current_half] += 1
        logger.info(f"⚽ ГОЛ в матче {match_id}! Тайм: {current_half}, всего голов в тайме: {self.half_goals[match_id][current_half]}")
    
    def _should_send_signal(self, prediction: Dict) -> bool:
        """Определяет, нужно ли отправлять сигнал"""
        if prediction.get('error', False):
            return False
        
        probability = prediction.get('total_goal_probability', 0)
        confidence = prediction.get('confidence_level', 'LOW')
        
        if confidence in ['HIGH', 'VERY_HIGH']:
            return True
        
        if confidence == 'MEDIUM' and probability >= self.thresholds['medium']:
            return True
        
        return False
    
    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        """Извлекает статистику для команды с использованием словаря синонимов"""
        stats = {
            'shots': 0,
            'shots_on_target': 0,
            'corners': 0,
            'possession': 50,
            'dangerous_attacks': 0,
            'xg': 0.5
        }
        
        if not match.stats:
            logger.debug(f"match.stats пуст для match.id={match.id}")
            return stats
        
        # Если match.stats уже является словарем, используем его
        if isinstance(match.stats, dict):
            logger.debug(f"match.stats является словарем для match.id={match.id}")
            
            # Извлекаем значения для конкретной команды
            if is_home:
                stats['shots'] = match.stats.get('shots_home', 0)
                stats['shots_on_target'] = match.stats.get('shots_ontarget_home', 0)
                stats['possession'] = match.stats.get('possession_home', 50)
                stats['corners'] = match.stats.get('corners_home', 0)
                stats['dangerous_attacks'] = match.stats.get('dangerous_attacks_home', 0)
                stats['xg'] = match.stats.get('xg_home', 0.5)
            else:
                stats['shots'] = match.stats.get('shots_away', 0)
                stats['shots_on_target'] = match.stats.get('shots_ontarget_away', 0)
                stats['possession'] = match.stats.get('possession_away', 50)
                stats['corners'] = match.stats.get('corners_away', 0)
                stats['dangerous_attacks'] = match.stats.get('dangerous_attacks_away', 0)
                stats['xg'] = match.stats.get('xg_away', 0.5)
            
            return stats
        
        # Если match.stats - объект с атрибутами
        if hasattr(match.stats, '__dict__'):
            logger.debug(f"match.stats является объектом для match.id={match.id}, конвертируем")
            stats_dict = match.stats.__dict__
            
            if is_home:
                stats['shots'] = stats_dict.get('shots_home', 0)
                stats['shots_on_target'] = stats_dict.get('shots_ontarget_home', 0)
                stats['possession'] = stats_dict.get('possession_home', 50)
                stats['corners'] = stats_dict.get('corners_home', 0)
                stats['dangerous_attacks'] = stats_dict.get('dangerous_attacks_home', 0)
                stats['xg'] = stats_dict.get('xg_home', 0.5)
            else:
                stats['shots'] = stats_dict.get('shots_away', 0)
                stats['shots_on_target'] = stats_dict.get('shots_ontarget_away', 0)
                stats['possession'] = stats_dict.get('possession_away', 50)
                stats['corners'] = stats_dict.get('corners_away', 0)
                stats['dangerous_attacks'] = stats_dict.get('dangerous_attacks_away', 0)
                stats['xg'] = stats_dict.get('xg_away', 0.5)
            
            return stats
        
        # Если match.stats - список (старый формат)
        if isinstance(match.stats, list):
            logger.debug(f"match.stats является списком для match.id={match.id}")
            team_id = match.home_team.id if is_home and match.home_team else None
            if not team_id and not is_home and match.away_team:
                team_id = match.away_team.id
            
            if not team_id:
                return stats
            
            team_stats_dict = {}
            for period_stats in match.stats:
                if period_stats.get('period') == 'ALL':
                    for team_stat in period_stats.get('groups', []):
                        if team_stat.get('teamId') == team_id:
                            items = team_stat.get('statisticsItems', [])
                            for item in items:
                                name = item.get('name', '').lower()
                                value = item.get('value', 0)
                                
                                if isinstance(value, str):
                                    try:
                                        if '%' in value:
                                            value = float(value.replace('%', ''))
                                        else:
                                            value = float(value)
                                    except:
                                        value = 0
                                
                                team_stats_dict[name] = value
            
            stats['shots'] = self._get_stat_value(team_stats_dict, 'shots', 0)
            stats['shots_on_target'] = self._get_stat_value(team_stats_dict, 'shots_on_target', 0)
            stats['corners'] = self._get_stat_value(team_stats_dict, 'corners', 0)
            stats['possession'] = self._get_stat_value(team_stats_dict, 'possession', 50)
            stats['dangerous_attacks'] = self._get_stat_value(team_stats_dict, 'dangerous_attacks', 0)
            stats['xg'] = self._get_stat_value(team_stats_dict, 'xg', 0.5)
            
            return stats
        
        logger.warning(f"match.stats имеет неожиданный тип {type(match.stats)} для match.id={match.id}")
        return stats
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Подготовка данных для обучения"""
        X = []
        y = []
        
        for pred in self.predictions_history[-500:]:
            if 'error' in pred and pred['error']:
                continue
            
            match = pred.get('match')
            if not match or not hasattr(match, 'total_goals'):
                continue
            
            features = self._extract_features(match, pred)
            X.append(features.flatten())
            y.append(1 if match.total_goals > 0 else 0)
        
        return np.array(X), np.array(y)
    
    def _add_to_history(self, prediction: Dict):
        """Добавление в историю и периодическое обновление моделей"""
        self.predictions_history.append(prediction)
        
        if len(self.predictions_history) > self.max_history_size:
            self.predictions_history = self.predictions_history[-self.max_history_size:]
        
        if len(self.predictions_history) % 50 == 0:
            self._update_weights_gradient()
            self._update_weights_ml()
            self._optimize_thresholds()
            self._adjust_thresholds_dynamically()
    
    def _update_weights_gradient(self):
        """Градиентное обновление весов"""
        try:
            if len(self.accuracy_stats['calibration_data']) < self.min_matches_for_update:
                return
            
            recent_matches = self.predictions_history[-100:]
            factor_errors = defaultdict(list)
            
            for pred in recent_matches:
                if 'error' in pred and pred['error']:
                    continue
                
                match = pred.get('match')
                if not match or not hasattr(match, 'total_goals'):
                    continue
                
                actual_goals = match.total_goals > 0
                predicted_prob = pred.get('total_goal_probability', 0)
                error = actual_goals - predicted_prob
                
                factors = {
                    'xg': pred.get('home_stats', {}).get('xg', 0.5) + pred.get('away_stats', {}).get('xg', 0.5),
                    'shots_ontarget': pred.get('home_stats', {}).get('shots_on_target', 0) + pred.get('away_stats', {}).get('shots_on_target', 0),
                    'team_form': (pred.get('home_form', {}).get('weighted_form', 0.5) + pred.get('away_form', {}).get('weighted_form', 0.5)) / 2,
                    'dangerous_attacks': pred.get('home_stats', {}).get('dangerous_attacks', 0) + pred.get('away_stats', {}).get('dangerous_attacks', 0),
                    'shots': pred.get('home_stats', {}).get('shots', 0) + pred.get('away_stats', {}).get('shots', 0),
                    'corners': pred.get('home_stats', {}).get('corners', 0) + pred.get('away_stats', {}).get('corners', 0),
                    'possession': (pred.get('home_stats', {}).get('possession', 50) + pred.get('away_stats', {}).get('possession', 50)) / 2,
                }
                
                for factor, value in factors.items():
                    if value > 0:
                        if factor in ['xg', 'team_form']:
                            normalized = value / 3.0
                        elif factor in ['shots_ontarget', 'dangerous_attacks']:
                            normalized = value / 20.0
                        elif factor in ['shots', 'corners']:
                            normalized = value / 30.0
                        else:
                            normalized = value / 100.0
                        
                        gradient = error * normalized * self.learning_rate
                        factor_errors[factor].append(gradient)
            
            new_weights = self.weights.copy()
            total_adjustment = 0
            
            for factor, gradients in factor_errors.items():
                if gradients and factor in new_weights:
                    avg_gradient = np.mean(gradients)
                    adjustment = avg_gradient * self.learning_rate * 10
                    new_weights[factor] = max(0.01, min(0.5, self.weights[factor] + adjustment))
                    total_adjustment += abs(adjustment)
                    
                    logger.debug(f"Фактор {factor}: {self.weights[factor]:.3f} -> {new_weights[factor]:.3f}")
            
            if total_adjustment > 0.01:
                total = sum(new_weights.values())
                if total > 0:
                    self.weights = {k: v/total for k, v in new_weights.items()}
                    self.weights_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'weights': self.weights.copy()
                    })
                    logger.info(f"✅ Веса обновлены: {self.weights}")
                    
                    if len(self.weights_history) > 100:
                        self.weights_history = self.weights_history[-100:]
        
        except Exception as e:
            logger.error(f"❌ Ошибка обновления весов: {e}")
    
    def _update_weights_ml(self):
        """Обновление весов через ML"""
        try:
            if len(self.accuracy_stats['calibration_data']) < self.min_matches_for_update:
                return
            
            X, y = self._prepare_training_data()
            if len(X) < self.min_matches_for_update:
                return
            
            X_scaled = self.scaler.fit_transform(X)
            self.ml_model.fit(X_scaled, y)
            
            if hasattr(self.ml_model, 'coef_'):
                importance = np.abs(self.ml_model.coef_[0])
                for name, imp in zip(self.feature_names, importance):
                    self.accuracy_stats['feature_importance'][name] = float(imp)
                
                logger.info(f"📊 Важность признаков: {self.accuracy_stats['feature_importance']}")
            
            joblib.dump(self.ml_model, self.model_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ML модели: {e}")
    
    def _optimize_thresholds(self):
        """Оптимизация порогов"""
        try:
            if len(self.accuracy_stats['calibration_data']) < 100:
                return
            
            recent_data = self.accuracy_stats['calibration_data'][-200:]
            best_thresholds = {}
            
            for level, default_threshold in [('low', 0.15), ('medium', 0.25), 
                                            ('high', 0.40), ('very_high', 0.55)]:
                best_acc = 0
                best_thresh = default_threshold
                
                for threshold in np.arange(0.1, 0.7, 0.05):
                    correct = 0
                    total = 0
                    
                    for prob, actual in recent_data:
                        if prob >= threshold:
                            total += 1
                            if actual == 1:
                                correct += 1
                    
                    if total > 0:
                        accuracy = correct / total
                        if accuracy > best_acc:
                            best_acc = accuracy
                            best_thresh = threshold
                
                if best_acc > 0.5:
                    best_thresholds[level] = best_thresh
            
            if best_thresholds:
                old_thresholds = self.thresholds.copy()
                self.thresholds.update(best_thresholds)
                logger.info(f"📊 Пороги оптимизированы: {old_thresholds} -> {self.thresholds}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации порогов: {e}")
    
    def _adjust_thresholds_dynamically(self):
        """Динамическая настройка порогов"""
        if len(self.accuracy_stats['calibration_data']) < 50:
            return
        
        recent_data = self.accuracy_stats['calibration_data'][-50:]
        percentiles = [70, 50, 30, 15]
        
        probabilities = [p for p, _ in recent_data]
        if not probabilities:
            return
        
        sorted_probs = sorted(probabilities)
        
        new_thresholds = {}
        levels = ['very_high', 'high', 'medium', 'low']
        
        for level, percentile in zip(levels, percentiles):
            idx = int(len(sorted_probs) * (100 - percentile) / 100)
            if idx < len(sorted_probs):
                new_thresholds[level] = sorted_probs[idx]
        
        for level in levels:
            if level in new_thresholds:
                old = self.thresholds[level]
                new = new_thresholds[level]
                self.thresholds[level] = old * 0.7 + new * 0.3
        
        logger.info(f"📊 Пороги динамически обновлены: {self.thresholds}")
    
    def _extract_features(self, match: Match, prediction: Dict) -> np.ndarray:
        """Извлечение признаков для ML"""
        features = []
        
        features.append(prediction.get('home_goal_probability', 0))
        features.append(prediction.get('away_goal_probability', 0))
        features.append(prediction.get('total_goal_probability', 0))
        
        if prediction.get('home_form'):
            features.append(prediction['home_form'].get('weighted_form', 0.5))
            features.append(prediction['home_form'].get('avg_xg_for', 1.0))
            features.append(prediction['home_form'].get('avg_xg_against', 1.0))
        else:
            features.extend([0.5, 1.0, 1.0])
        
        if prediction.get('away_form'):
            features.append(prediction['away_form'].get('weighted_form', 0.5))
            features.append(prediction['away_form'].get('avg_xg_for', 1.0))
            features.append(prediction['away_form'].get('avg_xg_against', 1.0))
        else:
            features.extend([0.5, 1.0, 1.0])
        
        features.append(prediction.get('home_stats', {}).get('xg', 0.5))
        features.append(prediction.get('away_stats', {}).get('xg', 0.5))
        features.append(prediction.get('home_stats', {}).get('shots_on_target', 0) / 10)
        features.append(prediction.get('away_stats', {}).get('shots_on_target', 0) / 10)
        
        league_level = self.league_levels.get(match.league_id, 2)
        features.append(league_level)
        
        minute_norm = (match.minute or 0) / 90
        features.append(minute_norm)
        
        return np.array(features).reshape(1, -1)
    
    def update_accuracy(self, prediction_id: str, actual_goals: int):
        """Обновление статистики точности"""
        try:
            for pred in self.predictions_history:
                if str(pred.get('match_id')) == str(prediction_id):
                    predicted_prob = pred.get('total_goal_probability', 0)
                    confidence = pred.get('confidence_level', 'MEDIUM')
                    minute = pred.get('minute', 0)
                    league_id = pred.get('league_id')
                    
                    had_goal = actual_goals > 0
                    predicted_goal = predicted_prob > 0.5
                    
                    self.accuracy_stats['total_predictions'] += 1
                    
                    self.accuracy_stats['calibration_data'].append(
                        (predicted_prob, 1 if had_goal else 0)
                    )
                    
                    if len(self.accuracy_stats['calibration_data']) > 1000:
                        self.accuracy_stats['calibration_data'] = \
                            self.accuracy_stats['calibration_data'][-1000:]
                    
                    if confidence in self.accuracy_stats['by_confidence']:
                        self.accuracy_stats['by_confidence'][confidence]['total'] += 1
                        if had_goal == predicted_goal:
                            self.accuracy_stats['by_confidence'][confidence]['correct'] += 1
                    
                    minute_range = (minute // 15) * 15
                    minute_key = f"{minute_range}-{minute_range+15}"
                    self.accuracy_stats['by_minute'][minute_key]['total'] += 1
                    if had_goal == predicted_goal:
                        self.accuracy_stats['by_minute'][minute_key]['correct'] += 1
                    
                    if league_id:
                        league_key = f"league_{league_id}"
                        self.accuracy_stats['by_league'][league_key]['total'] += 1
                        if had_goal == predicted_goal:
                            self.accuracy_stats['by_league'][league_key]['correct'] += 1
                    
                    if pred.get('signal'):
                        self.accuracy_stats['total_signals'] += 1
                        
                        if had_goal == predicted_goal:
                            self.accuracy_stats['correct_predictions'] += 1
                        else:
                            self.accuracy_stats['incorrect_predictions'] += 1
                    
                    self.accuracy_stats['goals_predicted'] += predicted_prob * 3
                    self.accuracy_stats['goals_actual'] += actual_goals
                    
                    total = self.accuracy_stats['correct_predictions'] + \
                            self.accuracy_stats['incorrect_predictions']
                    if total > 0:
                        self.accuracy_stats['accuracy_rate'] = \
                            self.accuracy_stats['correct_predictions'] / total
                    
                    self.accuracy_stats['last_updated'] = datetime.now().isoformat()
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка обновления статистики точности: {e}")
    
    def _get_default_prediction(self, match: Match) -> Dict:
        """Предсказание по умолчанию"""
        return {
            'match_id': match.id,
            'match': match,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'home_goal_probability': 0.3,
            'away_goal_probability': 0.3,
            'total_goal_probability': 0.5,
            'confidence_level': 'LOW',
            'signal': None,
            'home_stats': {},
            'away_stats': {},
            'error': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_accuracy_stats(self) -> Dict:
        """Статистика точности"""
        return self.accuracy_stats.copy()
    
    def get_weights_history(self) -> List:
        """История весов"""
        return self.weights_history.copy()
    
    def get_statistics(self) -> Dict:
        """Полная статистика"""
        if not self.predictions_history:
            return {
                'total_predictions': 0,
                'avg_probability': 0,
                'signals_sent': self.accuracy_stats['total_signals'],
                'confidence_distribution': {},
                'feature_importance': self.accuracy_stats['feature_importance'],
                'current_weights': self.weights,
                'thresholds': self.thresholds,
                'by_confidence': self.accuracy_stats['by_confidence'],
                'by_minute': dict(self.accuracy_stats['by_minute']),
                'by_league': dict(self.accuracy_stats['by_league']),
                'regression_stats': self.accuracy_stats.get('regression_stats', {}),
                'poisson_stats': self.accuracy_stats.get('poisson_stats', {})
            }
        
        total = len(self.predictions_history)
        signals = [p for p in self.predictions_history if p.get('signal')]
        
        confidence_dist = defaultdict(int)
        for p in self.predictions_history:
            confidence_dist[p.get('confidence_level', 'UNKNOWN')] += 1
        
        for k in confidence_dist:
            confidence_dist[k] = confidence_dist[k] / total
        
        return {
            'total_predictions': total,
            'avg_probability': np.mean([p.get('total_goal_probability', 0) for p in self.predictions_history]),
            'signals_sent': self.accuracy_stats['total_signals'],
            'signal_rate': len(signals) / total if total > 0 else 0,
            'confidence_distribution': dict(confidence_dist),
            'feature_importance': self.accuracy_stats['feature_importance'],
            'current_weights': self.weights,
            'thresholds': self.thresholds,
            'by_confidence': self.accuracy_stats['by_confidence'],
            'by_minute': dict(self.accuracy_stats['by_minute']),
            'by_league': dict(self.accuracy_stats['by_league']),
            'regression_stats': self.accuracy_stats.get('regression_stats', {}),
            'poisson_stats': self.accuracy_stats.get('poisson_stats', {})
        }
    
    def save_predictions(self, filename: str = 'data/predictions.json'):
        """Сохранение предсказаний"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            data = {
                'predictions': [],
                'weights_history': self.weights_history,
                'accuracy_stats': self.accuracy_stats,
                'thresholds': self.thresholds,
                'half_goals': self.half_goals,
                'half_signals': self.half_signals,
                'match_last_signal': {str(k): v.isoformat() if isinstance(v, datetime) else str(v) 
                                     for k, v in self.match_last_signal.items()},
                'match_signal_count': self.match_signal_count
            }
            
            for p in self.predictions_history:
                p_copy = p.copy()
                if 'match' in p_copy:
                    del p_copy['match']
                if 'signal' in p_copy and p_copy['signal']:
                    if 'timestamp' in p_copy['signal']:
                        p_copy['signal']['timestamp'] = p_copy['signal']['timestamp'].isoformat()
                data['predictions'].append(p_copy)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Сохранено {len(data['predictions'])} предсказаний в {filename}")
            
            if self.ml_model:
                joblib.dump(self.ml_model, self.model_path)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения предсказаний: {e}")
    
    def load_predictions(self, filename: str = 'data/predictions.json'):
        """Загрузка предсказаний"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.predictions_history = data.get('predictions', [])
                self.weights_history = data.get('weights_history', [])
                self.accuracy_stats.update(data.get('accuracy_stats', {}))
                self.thresholds.update(data.get('thresholds', self.thresholds))
                self.half_goals = data.get('half_goals', {})
                self.half_signals = data.get('half_signals', {})
                
                # Загружаем данные о сигналах
                match_last_signal = data.get('match_last_signal', {})
                self.match_last_signal = {}
                for k, v in match_last_signal.items():
                    try:
                        self.match_last_signal[int(k)] = datetime.fromisoformat(v)
                    except:
                        pass
                
                self.match_signal_count = data.get('match_signal_count', {})
                
                logger.info(f"Загружено {len(self.predictions_history)} предсказаний из {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки предсказаний: {e}")