# statistical_models.py
import numpy as np
from scipy import stats
from scipy.special import comb
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class StatisticalModels:
    """
    Класс для статистического моделирования футбольных матчей
    Включает: Пуассон-регрессию, байесовские методы, анализ временных рядов
    """
    
    def __init__(self):
        self.models = {}
        self.results_cache = {}
        self.feature_names = []
        
    def poisson_probability(self, lambda_: float, k: int) -> float:
        """
        Вероятность Пуассона P(X = k) = (e^{-λ} * λ^k) / k!
        
        Args:
            lambda_: Интенсивность (среднее количество голов)
            k: Количество голов
            
        Returns:
            float: Вероятность
        """
        return stats.poisson.pmf(k, lambda_)
    
    def poisson_cumulative(self, lambda_: float, k: int) -> float:
        """
        Накопительная функция распределения Пуассона P(X ≤ k)
        """
        return stats.poisson.cdf(k, lambda_)
    
    def match_goal_probabilities(self, home_lambda: float, away_lambda: float) -> Dict:
        """
        Рассчитывает вероятности различных исходов матча по Пуассону
        
        Args:
            home_lambda: Среднее голов хозяев
            away_lambda: Среднее голов гостей
            
        Returns:
            Dict с вероятностями
        """
        max_goals = 10
        probs = {}
        
        # Вероятности точного счета
        exact_scores = {}
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                prob = self.poisson_probability(home_lambda, i) * \
                       self.poisson_probability(away_lambda, j)
                exact_scores[f"{i}:{j}"] = prob
        
        # Вероятности исходов
        home_win = sum(prob for (score, prob) in exact_scores.items() 
                      if int(score.split(':')[0]) > int(score.split(':')[1]))
        away_win = sum(prob for (score, prob) in exact_scores.items() 
                      if int(score.split(':')[0]) < int(score.split(':')[1]))
        draw = sum(prob for (score, prob) in exact_scores.items() 
                  if int(score.split(':')[0]) == int(score.split(':')[1]))
        
        # Вероятность тотала
        total_probs = {}
        for total in range(max_goals * 2 + 1):
            total_probs[total] = sum(prob for (score, prob) in exact_scores.items()
                                     if int(score.split(':')[0]) + int(score.split(':')[1]) == total)
        
        return {
            'exact_scores': exact_scores,
            'home_win': home_win,
            'away_win': away_win,
            'draw': draw,
            'total_goals': total_probs,
            'over_0.5': 1 - total_probs.get(0, 0),
            'over_1.5': 1 - total_probs.get(0, 0) - total_probs.get(1, 0),
            'over_2.5': 1 - sum(total_probs.get(i, 0) for i in range(3))
        }
    
    def bayesian_update(self, prior_mean: float, prior_var: float,
                        observed_data: List[float]) -> Dict:
        """
        Байесовское обновление для нормального распределения
        
        Args:
            prior_mean: Априорное среднее
            prior_var: Априорная дисперсия
            observed_data: Наблюдаемые данные
            
        Returns:
            Dict с апостериорными параметрами
        """
        n = len(observed_data)
        sample_mean = np.mean(observed_data)
        sample_var = np.var(observed_data, ddof=1) if n > 1 else prior_var
        
        # Апостериорные параметры
        posterior_var = 1 / (1/prior_var + n/sample_var)
        posterior_mean = posterior_var * (prior_mean/prior_var + n*sample_mean/sample_var)
        
        # Доверительный интервал
        ci_lower, ci_upper = stats.norm.interval(0.95, loc=posterior_mean, 
                                                  scale=np.sqrt(posterior_var))
        
        return {
            'posterior_mean': posterior_mean,
            'posterior_var': posterior_var,
            'posterior_std': np.sqrt(posterior_var),
            'ci_95': (ci_lower, ci_upper),
            'sample_size': n
        }


class MonteCarloSimulator:
    """
    Класс для Монте-Карло симуляций
    """
    
    def __init__(self, n_simulations: int = 10000):
        self.n_simulations = n_simulations
        self.results = []
        
    def simulate_match(self, home_lambda: float, away_lambda: float,
                        home_std: float = 0.2, away_std: float = 0.2) -> Dict:
        """
        Симуляция матча методом Монте-Карло
        
        Args:
            home_lambda: Среднее голов хозяев
            away_lambda: Среднее голов гостей
            home_std: Стандартное отклонение для хозяев
            away_std: Стандартное отклонение для гостей
            
        Returns:
            Dict с результатами симуляции
        """
        home_goals = []
        away_goals = []
        
        for _ in range(self.n_simulations):
            # Добавляем случайность в интенсивность
            home_rand = np.random.normal(1, home_std)
            away_rand = np.random.normal(1, away_std)
            
            home_intensity = max(0, home_lambda * home_rand)
            away_intensity = max(0, away_lambda * away_rand)
            
            home_goals.append(np.random.poisson(home_intensity))
            away_goals.append(np.random.poisson(away_intensity))
        
        home_goals = np.array(home_goals)
        away_goals = np.array(away_goals)
        
        # Расчет вероятностей
        home_wins = np.sum(home_goals > away_goals) / self.n_simulations
        away_wins = np.sum(home_goals < away_goals) / self.n_simulations
        draws = np.sum(home_goals == away_goals) / self.n_simulations
        
        # Распределение тоталов
        totals = home_goals + away_goals
        total_dist = {}
        for total in range(0, 11):
            total_dist[total] = np.sum(totals == total) / self.n_simulations
        
        # Value at Risk (VaR)
        var_95 = np.percentile(totals, 5)
        var_99 = np.percentile(totals, 1)
        
        # Bootstrap-оценки
        bootstrap_means = []
        for _ in range(1000):
            sample = np.random.choice(totals, size=len(totals), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        ci_lower, ci_upper = np.percentile(bootstrap_means, [2.5, 97.5])
        
        return {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'home_goals_mean': np.mean(home_goals),
            'away_goals_mean': np.mean(away_goals),
            'total_mean': np.mean(totals),
            'total_std': np.std(totals),
            'total_distribution': total_dist,
            'var_95': var_95,
            'var_99': var_99,
            'bootstrap_ci': (ci_lower, ci_upper),
            'percentiles': {
                '10%': np.percentile(totals, 10),
                '25%': np.percentile(totals, 25),
                '50%': np.percentile(totals, 50),
                '75%': np.percentile(totals, 75),
                '90%': np.percentile(totals, 90)
            }
        }


class TimeSeriesAnalyzer:
    """
    Класс для анализа временных рядов
    """
    
    def __init__(self):
        self.results = {}
        
    def moving_average(self, series: np.ndarray, window: int = 5) -> np.ndarray:
        """
        Скользящее среднее
        
        Args:
            series: Временной ряд
            window: Размер окна
            
        Returns:
            np.ndarray: Скользящее среднее
        """
        return np.convolve(series, np.ones(window)/window, mode='valid')
    
    def exponential_moving_average(self, series: np.ndarray, alpha: float = 0.3) -> np.ndarray:
        """
        Экспоненциальное скользящее среднее
        
        Args:
            series: Временной ряд
            alpha: Коэффициент сглаживания
            
        Returns:
            np.ndarray: EMA
        """
        ema = np.zeros_like(series)
        ema[0] = series[0]
        for t in range(1, len(series)):
            ema[t] = alpha * series[t] + (1 - alpha) * ema[t-1]
        return ema