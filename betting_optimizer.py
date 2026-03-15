# betting_optimizer.py
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BettingOptimizer:
    """
    Класс для оптимизации ставок на основе математических моделей
    Включает: критерий Келли, метрики эффективности, управление рисками
    """
    
    def __init__(self, initial_bankroll: float = 1000.0):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.bet_history = []
        self.daily_results = {}
        
    def kelly_criterion(self, probability: float, odds: float) -> float:
        """
        Критерий Келли для оптимального размера ставки
        
        Args:
            probability: Ваша оценка вероятности (0-1)
            odds: Коэффициент букмекера (десятичный)
            
        Returns:
            float: Доля банкролла для ставки (0-1)
        """
        # Имплицитная вероятность букмекера
        implied_prob = 1 / odds
        
        # Преимущество (edge)
        edge = probability - implied_prob
        
        if edge <= 0:
            return 0.0
        
        # Критерий Келли: f* = (p * (odds-1) - (1-p)) / (odds-1)
        kelly_fraction = (probability * (odds - 1) - (1 - probability)) / (odds - 1)
        
        # Ограничиваем максимальную ставку
        return max(0.0, min(kelly_fraction, 0.25))  # Не больше 25% банкролла
    
    def fractional_kelly(self, probability: float, odds: float, 
                          fraction: float = 0.5) -> float:
        """
        Дробный критерий Келли (более консервативный)
        
        Args:
            probability: Ваша оценка вероятности
            odds: Коэффициент
            fraction: Доля от полного Келли (0.25-0.5 рекомендуется)
            
        Returns:
            float: Доля банкролла для ставки
        """
        full_kelly = self.kelly_criterion(probability, odds)
        return full_kelly * fraction
    
    def expected_value(self, probability: float, odds: float) -> float:
        """
        Ожидаемое значение (Expected Value) ставки
        
        Args:
            probability: Ваша оценка вероятности
            odds: Коэффициент
            
        Returns:
            float: EV (положительное значение означает преимущество)
        """
        return (probability * odds) - 1
    
    def expected_utility(self, probability: float, odds: float, 
                          bankroll: float, risk_aversion: float = 1.0) -> float:
        """
        Ожидаемая полезность с учетом неприятия риска
        
        Args:
            probability: Вероятность
            odds: Коэффициент
            bankroll: Текущий банкролл
            risk_aversion: Коэффициент неприятия риска (больше = осторожнее)
            
        Returns:
            float: Ожидаемая полезность
        """
        win_utility = np.log(bankroll * (1 + odds - 1))
        lose_utility = np.log(bankroll * 0.5)  # Проигрыш половины ставки
        return probability * win_utility + (1 - probability) * lose_utility
    
    def place_bet(self, probability: float, odds: float, stake: float) -> Dict:
        """
        Размещение ставки и обновление банкролла
        
        Args:
            probability: Оценка вероятности
            odds: Коэффициент
            stake: Сумма ставки
            
        Returns:
            Dict с результатом
        """
        if stake > self.current_bankroll:
            stake = self.current_bankroll
            logger.warning(f"Ставка урезана до доступного банкролла: {stake}")
        
        bet = {
            'timestamp': datetime.now().isoformat(),
            'probability': probability,
            'odds': odds,
            'stake': stake,
            'expected_value': self.expected_value(probability, odds),
            'kelly_fraction': self.kelly_criterion(probability, odds),
            'status': 'pending'
        }
        
        self.bet_history.append(bet)
        self.current_bankroll -= stake
        
        return bet
    
    def settle_bet(self, bet_index: int, won: bool) -> Dict:
        """
        Расчет результата ставки
        
        Args:
            bet_index: Индекс ставки в истории
            won: True если ставка выиграла
            
        Returns:
            Dict с обновленным банкроллом
        """
        if bet_index >= len(self.bet_history):
            raise ValueError("Неверный индекс ставки")
        
        bet = self.bet_history[bet_index]
        
        if won:
            profit = bet['stake'] * (bet['odds'] - 1)
            self.current_bankroll += bet['stake'] + profit
            bet['profit'] = profit
            bet['status'] = 'won'
        else:
            bet['profit'] = -bet['stake']
            bet['status'] = 'lost'
        
        bet['bankroll_after'] = self.current_bankroll
        
        # Обновляем дневную статистику
        date = bet['timestamp'][:10]
        if date not in self.daily_results:
            self.daily_results[date] = {'profit': 0, 'bets': 0, 'won': 0}
        
        self.daily_results[date]['profit'] += bet['profit']
        self.daily_results[date]['bets'] += 1
        if won:
            self.daily_results[date]['won'] += 1
        
        return bet
    
    def sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Коэффициент Шарпа (доходность с поправкой на риск)
        
        Args:
            returns: Список доходностей
            risk_free_rate: Безрисковая ставка (годовая)
            
        Returns:
            float: Коэффициент Шарпа
        """
        returns = np.array(returns)
        excess_returns = returns - risk_free_rate / 252  # Дневная безрисковая
        
        if np.std(returns) == 0:
            return 0.0
        
        return np.mean(excess_returns) / np.std(returns) * np.sqrt(252)
    
    def sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Коэффициент Сортино (учитывает только отрицательную волатильность)
        
        Args:
            returns: Список доходностей
            risk_free_rate: Безрисковая ставка
            
        Returns:
            float: Коэффициент Сортино
        """
        returns = np.array(returns)
        excess_returns = returns - risk_free_rate / 252
        
        # Только отрицательные доходности
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0:
            return np.mean(excess_returns) * np.sqrt(252) if np.mean(excess_returns) > 0 else 0.0
        
        downside_deviation = np.std(negative_returns)
        
        if downside_deviation == 0:
            return 0.0
        
        return np.mean(excess_returns) / downside_deviation * np.sqrt(252)
    
    def calmar_ratio(self, returns: List[float]) -> float:
        """
        Коэффициент Кальмара (доходность / максимальная просадка)
        
        Args:
            returns: Список доходностей
            
        Returns:
            float: Коэффициент Кальмара
        """
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)
        
        # Максимальная просадка
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(np.min(drawdown))
        
        if max_drawdown == 0:
            return 0.0
        
        # Годовая доходность
        total_return = cumulative[-1] - 1
        years = len(returns) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
        
        return annual_return / max_drawdown
    
    def maximum_drawdown(self, returns: List[float]) -> Dict:
        """
        Максимальная просадка и связанные метрики
        
        Args:
            returns: Список доходностей
            
        Returns:
            Dict с информацией о просадке
        """
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)
        
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        
        # Длительность просадки
        recovery_idx = max_dd_idx
        while recovery_idx < len(drawdown) and drawdown[recovery_idx] < 0:
            recovery_idx += 1
        
        dd_duration = recovery_idx - max_dd_idx if recovery_idx < len(drawdown) else len(drawdown) - max_dd_idx
        
        return {
            'max_drawdown': abs(max_dd),
            'max_drawdown_date': max_dd_idx,
            'drawdown_duration': dd_duration,
            'current_drawdown': drawdown[-1] if drawdown[-1] < 0 else 0
        }
    
    def profit_factor(self, returns: List[float]) -> float:
        """
        Profit Factor (сумма выигрышей / сумма проигрышей)
        
        Args:
            returns: Список доходностей
            
        Returns:
            float: Profit Factor (>1 прибыльно)
        """
        gains = sum(r for r in returns if r > 0)
        losses = abs(sum(r for r in returns if r < 0))
        
        if losses == 0:
            return float('inf') if gains > 0 else 1.0
        
        return gains / losses
    
    def roi(self, returns: List[float]) -> float:
        """
        Return on Investment
        
        Args:
            returns: Список доходностей
            
        Returns:
            float: ROI в процентах
        """
        total_return = np.prod(1 + np.array(returns)) - 1
        return total_return * 100
    
    def get_performance_report(self) -> Dict:
        """
        Полный отчет по эффективности
        
        Returns:
            Dict со всеми метриками
        """
        if not self.bet_history:
            return {'error': 'Нет данных о ставках'}
        
        # Собираем доходности
        returns = [bet['profit'] / self.initial_bankroll 
                   for bet in self.bet_history if bet['status'] != 'pending']
        
        if not returns:
            return {'error': 'Нет завершенных ставок'}
        
        report = {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'total_profit': self.current_bankroll - self.initial_bankroll,
            'roi_percent': self.roi(returns),
            'total_bets': len([b for b in self.bet_history if b['status'] != 'pending']),
            'won_bets': len([b for b in self.bet_history if b['status'] == 'won']),
            'lost_bets': len([b for b in self.bet_history if b['status'] == 'lost']),
            'win_rate': len([b for b in self.bet_history if b['status'] == 'won']) / 
                       len([b for b in self.bet_history if b['status'] != 'pending']) * 100,
            'sharpe_ratio': self.sharpe_ratio(returns),
            'sortino_ratio': self.sortino_ratio(returns),
            'calmar_ratio': self.calmar_ratio(returns),
            'profit_factor': self.profit_factor(returns),
            'max_drawdown': self.maximum_drawdown(returns),
            'avg_bet_size': np.mean([b['stake'] for b in self.bet_history]),
            'avg_odds': np.mean([b['odds'] for b in self.bet_history]),
            'avg_probability': np.mean([b['probability'] for b in self.bet_history]),
            'daily_stats': self.daily_results
        }
        
        return report