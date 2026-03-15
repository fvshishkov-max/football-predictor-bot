# statistical_models.py
import numpy as np
from scipy import stats
from scipy.special import comb
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import Poisson, NegativeBinomial
from statsmodels.discrete.count_model import ZeroInflatedPoisson
from statsmodels.stats.outliers_influence import variance_inflation_factor
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
        
    def fit_poisson_regression(self, X: np.ndarray, y: np.ndarray, 
                                feature_names: List[str]) -> Dict:
        """
        Пуассон-регрессия для моделирования количества голов
        
        Args:
            X: Матрица признаков
            y: Целевая переменная (количество голов)
            feature_names: Названия признаков
            
        Returns:
            Dict с результатами модели
        """
        try:
            # Добавляем константу
            X_with_const = sm.add_constant(X)
            
            # Обучаем Пуассон-регрессию
            poisson_model = sm.Poisson(y, X_with_const)
            poisson_results = poisson_model.fit(disp=0)
            
            # Извлекаем статистику
            results = {
                'model': poisson_model,
                'results': poisson_results,
                'params': dict(zip(['const'] + feature_names, poisson_results.params)),
                'pvalues': dict(zip(['const'] + feature_names, poisson_results.pvalues)),
                'conf_int': poisson_results.conf_int().tolist(),
                'aic': poisson_results.aic,
                'bic': poisson_results.bic,
                'log_likelihood': poisson_results.llf,
                'pseudo_r_squared': 1 - poisson_results.llf / poisson_results.llnull,
                'feature_names': ['const'] + feature_names,
                'method': 'poisson'
            }
            
            logger.info(f"✅ Пуассон-регрессия обучена: AIC={results['aic']:.2f}, "
                       f"R²={results['pseudo_r_squared']:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения Пуассон-регрессии: {e}")
            return {}
    
    def fit_negative_binomial(self, X: np.ndarray, y: np.ndarray,
                               feature_names: List[str]) -> Dict:
        """
        Отрицательное биномиальное распределение (лучше для передисперсии)
        """
        try:
            X_with_const = sm.add_constant(X)
            nb_model = NegativeBinomial(y, X_with_const)
            nb_results = nb_model.fit(disp=0)
            
            results = {
                'model': nb_model,
                'results': nb_results,
                'params': dict(zip(['const'] + feature_names, nb_results.params)),
                'pvalues': dict(zip(['const'] + feature_names, nb_results.pvalues)),
                'aic': nb_results.aic,
                'bic': nb_results.bic,
                'log_likelihood': nb_results.llf,
                'method': 'negative_binomial'
            }
            
            logger.info(f"✅ Negative Binomial обучена: AIC={results['aic']:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка Negative Binomial: {e}")
            return {}
    
    def fit_zero_inflated_poisson(self, X: np.ndarray, y: np.ndarray,
                                    feature_names: List[str]) -> Dict:
        """
        Zero-Inflated Poisson для матчей с избыточными нулями
        """
        try:
            X_with_const = sm.add_constant(X)
            zip_model = ZeroInflatedPoisson(y, X_with_const, X_with_const)
            zip_results = zip_model.fit(disp=0, maxiter=100)
            
            results = {
                'model': zip_model,
                'results': zip_results,
                'params': dict(zip(['const'] + feature_names, zip_results.params[:len(feature_names)+1])),
                'inflate_params': zip_results.params[len(feature_names)+1:],
                'aic': zip_results.aic,
                'bic': zip_results.bic,
                'log_likelihood': zip_results.llf,
                'method': 'zero_inflated_poisson'
            }
            
            logger.info(f"✅ Zero-Inflated Poisson обучена: AIC={results['aic']:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка ZIP: {e}")
            return {}
    
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
    
    def granger_causality(self, data1: np.ndarray, data2: np.ndarray, 
                           cause_idx: int = 0, effect_idx: int = 1,
                           max_lag: int = 5) -> Dict:
        """
        Тест Грэнджера на причинность для временных рядов
        
        Args:
            data1: Первый временной ряд
            data2: Второй временной ряд
            cause_idx: Индекс причины (0 - data1, 1 - data2)
            effect_idx: Индекс следствия
            max_lag: Максимальный лаг
            
        Returns:
            Dict с результатами теста
        """
        from statsmodels.tsa.stattools import grangercausalitytests
        
        try:
            # Создаем матрицу данных
            data = np.column_stack([data1, data2])
            
            gc_result = grangercausalitytests(data, max_lag, verbose=False)
            
            results = {}
            for lag in range(1, max_lag + 1):
                p_value = gc_result[lag][0]['ssr_ftest'][1]
                f_stat = gc_result[lag][0]['ssr_ftest'][0]
                results[lag] = {
                    'f_statistic': f_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка теста Грэнджера: {e}")
            return {}


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
        
    def adf_test(self, series: np.ndarray, series_name: str = 'series') -> Dict:
        """
        Тест Дики-Фуллера на стационарность
        
        Args:
            series: Временной ряд
            series_name: Название ряда
            
        Returns:
            Dict с результатами теста
        """
        from statsmodels.tsa.stattools import adfuller
        
        result = adfuller(series, autolag='AIC')
        
        return {
            'series_name': series_name,
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05,
            'used_lag': result[2],
            'nobs': result[3]
        }
    
    def autocorrelation(self, series: np.ndarray, lags: int = 20) -> Dict:
        """
        Расчет автокорреляции
        
        Args:
            series: Временной ряд
            lags: Количество лагов
            
        Returns:
            Dict с автокорреляциями
        """
        n = len(series)
        mean = np.mean(series)
        var = np.var(series)
        
        autocorr = {}
        for lag in range(1, min(lags, n) + 1):
            if lag >= n:
                autocorr[lag] = 0
                continue
                
            cov = np.sum((series[:-lag] - mean) * (series[lag:] - mean)) / n
            autocorr[lag] = cov / var
        
        # Тест Льюнга-Бокса
        q_stat = n * (n + 2) * np.sum([autocorr[l]**2 / (n - l) 
                                        for l in range(1, min(lags, n) + 1)])
        p_value = 1 - stats.chi2.cdf(q_stat, df=min(lags, n))
        
        return {
            'autocorrelations': autocorr,
            'q_statistic': q_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
    
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