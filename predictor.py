# predictor.py
import logging
import json
import csv
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from models import Match, LiveStats, GoalSignal, MatchAnalysis
from xg_provider import XGManager
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class Predictor:
    """Класс для анализа футбольных матчей в реальном времени с самообучением и xG"""
    
    # Критические таймы для голов (минуты)
    CRITICAL_TIMES = [15, 30, 45, 60, 75, 90]
    
    # Веса для разных типов статистики
    DEFAULT_WEIGHTS = {
        'xg': 0.35,
        'shots_ontarget': 0.25,
        'dangerous_attacks': 0.15,
        'shots': 0.10,
        'corners': 0.10,
        'possession': 0.05
    }
    
    # Пороги для разных таймов
    THRESHOLDS = {
        15: 0.70,
        30: 0.60,
        45: 0.55,
        60: 0.50,
        75: 0.45,
        90: 0.40
    }
    
    def __init__(self):
        self.analysis_intervals = self.CRITICAL_TIMES
        self.xg_manager = XGManager()
        
        self.params = {
            'shots_per_goal': 9.5,
            'ontarget_per_goal': 3.8,
            'corners_per_goal': 5.2,
            'dangerous_attack_per_goal': 2.5,
            'xg_per_goal': 1.2,
            'min_minutes_for_analysis': 5,
            'probability_threshold': 0.5,
            'high_probability_threshold': 0.7,
            'learning_rate': 0.05,
            'min_confidence': 0.3,
            'max_confidence': 0.95,
            'xg_weight_decay': 0.98,
            'use_xg': True,
            'min_send_probability': 50.0  # Минимальная вероятность для отправки
        }
        
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.thresholds = self.THRESHOLDS.copy()
        
        self.accuracy_stats = {
            'total_signals': 0,
            'correct_signals': 0,
            'accuracy_rate': 0,
            'avg_time_error': 0,
            'goals_predicted': 0,
            'goals_actual': 0,
            'xg_accuracy': 0,
            'signals_by_time': {t: {'total': 0, 'correct': 0} for t in self.CRITICAL_TIMES},
            'league_stats': defaultdict(lambda: {'total': 0, 'correct': 0, 'avg_xg': 0}),
            'team_stats': defaultdict(lambda: {'signals': 0, 'goals': 0, 'avg_xg': 0})
        }
        
        self.cache = {
            'match_analysis': {},
            'match_xg': {},
            'team_signals': defaultdict(set),
            'cache_ttl': 60
        }
        
        self.signals_history = []
        self.history_lock = threading.RLock()
        self.save_queue = deque(maxlen=100)
        self.last_save_time = 0
        self.save_interval = 10
        
        self._load_accuracy_stats()
        self._load_signals_history()
        self._load_weights()
        self._load_thresholds()
        self._load_xg_stats()
        
        self.start_auto_save()
        
        logger.info(f"📊 Модель инициализирована с порогами: {self.thresholds}")
        logger.info(f"⚖️ Начальные веса: {self.weights}")
    
    def _load_accuracy_stats(self):
        try:
            if os.path.exists('signal_accuracy.json'):
                with open('signal_accuracy.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accuracy_stats.update(data.get('stats', {}))
                    self.params.update(data.get('params', {}))
                logger.info(f"📊 Загружена статистика: сигналов {self.accuracy_stats['total_signals']}")
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
    
    def _load_weights(self):
        try:
            if os.path.exists('model_weights.json'):
                with open('model_weights.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.weights.update(data.get('weights', {}))
                logger.info(f"⚖️ Загружены веса модели: {self.weights}")
        except Exception as e:
            logger.error(f"Ошибка загрузки весов: {e}")
    
    def _load_thresholds(self):
        try:
            if os.path.exists('model_thresholds.json'):
                with open('model_thresholds.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    thresholds = {}
                    for k, v in data.get('thresholds', {}).items():
                        try:
                            thresholds[int(k)] = v
                        except (ValueError, TypeError):
                            thresholds[k] = v
                    self.thresholds.update(thresholds)
                logger.info(f"🎯 Загружены пороги: {self.thresholds}")
        except Exception as e:
            logger.error(f"Ошибка загрузки порогов: {e}")
    
    def _load_signals_history(self):
        try:
            if os.path.exists('signals_history_latest.json'):
                with open('signals_history_latest.json', 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        self.signals_history = loaded
                        self.accuracy_stats['total_signals'] = len(loaded)
                        self.accuracy_stats['goals_predicted'] = len(loaded)
                logger.info(f"📥 Загружено {len(self.signals_history)} сигналов")
        except Exception as e:
            logger.error(f"Ошибка загрузки истории: {e}")
    
    def _load_xg_stats(self):
        try:
            if os.path.exists('xg_stats.json'):
                with open('xg_stats.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accuracy_stats['xg_accuracy'] = data.get('xg_accuracy', 0)
                    self.params['xg_per_goal'] = data.get('xg_per_goal', 1.2)
                    if 'xg_weight' in data:
                        self.weights['xg'] = data['xg_weight']
                logger.info(f"🎯 Загружена статистика xG")
        except Exception as e:
            logger.error(f"Ошибка загрузки xG статистики: {e}")
    
    async def analyze_live_match(self, match: Match, stats: LiveStats) -> MatchAnalysis:
    """Анализирует live матч с использованием xG"""
    cache_key = match.id
    cached = self.cache['match_analysis'].get(cache_key)
    if cached:
        timestamp, analysis = cached
        if time.time() - timestamp < self.cache['cache_ttl']:
            return analysis
    
    if not stats:
        stats = LiveStats(minute=match.minute or 0)
    
    current_minute = match.minute or 0
    current_goals = (match.home_score or 0) + (match.away_score or 0)
    
    # Получаем xG данные
    xg_data = None
    if self.params['use_xg']:
        if match.id in self.cache['match_xg']:
            xg_data = self.cache['match_xg'][match.id]
        else:
            try:
                # Определяем лигу для Understat
                league_name = self.xg_manager.providers['understat'].get_league_name(match.league_id)
                
                # Получаем xG с автоматическим поиском
                xg_data = await self.xg_manager.get_xg(
                    match_id=match.id,
                    home_team=match.home_team.name,
                    away_team=match.away_team.name,
                    league=league_name,
                    match_date=match.start_time
                )
                if xg_data:
                    self.cache['match_xg'][match.id] = xg_data
                    logger.info(f"📊 xG для матча {match.id}: {xg_data['home_xg']:.2f}-{xg_data['away_xg']:.2f}")
            except Exception as e:
                logger.error(f"Ошибка получения xG для матча {match.id}: {e}")
    
    # Получаем факторы лиги и команд
    league_factor = self._get_league_factor(match.league_id, match.league_name)
    team_factor = self._get_team_factor(match.home_team.id, match.away_team.id)
    
    # Рассчитываем активность
    activity_level, activity_description = self._calculate_activity(stats, current_minute)
    
    # Находим следующий сигнал с учетом xG
    next_signal = await self._find_next_goal_signal(
        stats, current_minute, current_goals, match,
        league_factor, team_factor, xg_data
    )
    
    # Рассчитываем атакующий потенциал с учетом xG
    attack_potential = self._calculate_attack_potential(stats, current_minute, xg_data)
    
    analysis = MatchAnalysis(
        match_id=match.id,
        timestamp=datetime.now(),
        minute=current_minute,
        score=f"{match.home_score}:{match.away_score}",
        stats=stats,
        activity_level=activity_level,
        activity_description=activity_description,
        attack_potential=attack_potential,
        next_signal=next_signal,
        has_signal=next_signal is not None,
        xg_data=xg_data
    )
    
    self.cache['match_analysis'][cache_key] = (time.time(), analysis)
    
    if next_signal and xg_data:
        logger.info(f"⚽ Сигнал с xG {xg_data['total_xg']:.2f}: {match.home_team.name}-{match.away_team.name} "
                   f"~{next_signal.predicted_minute}' ({next_signal.probability:.1f}%)")
    
    return analysis
    
    def _get_league_factor(self, league_id: int, league_name: str) -> float:
        if not league_id:
            return 1.0
        stats = self.accuracy_stats['league_stats'].get(str(league_id))
        if not stats or stats['total'] < 5:
            return 1.0
        accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.5
        factor = 1.1 if accuracy > 0.7 else 0.9 if accuracy < 0.3 else 1.0
        return factor
    
    def _get_team_factor(self, home_id: int, away_id: int) -> float:
        home_stats = self.accuracy_stats['team_stats'].get(str(home_id), {})
        away_stats = self.accuracy_stats['team_stats'].get(str(away_id), {})
        factor = 1.0
        for stats in [home_stats, away_stats]:
            if stats and stats.get('signals', 0) > 0:
                avg_xg = stats.get('avg_xg', 0)
                factor *= 1.1 if avg_xg > 1.5 else 0.95 if avg_xg < 0.5 else 1.0
        return factor
    
    def _calculate_activity(self, stats: LiveStats, current_minute: int) -> tuple:
        if current_minute < self.params['min_minutes_for_analysis']:
            return 'Низкая', 'Матч только начался, нужно больше данных'
        
        shots_per_minute = stats.total_shots / current_minute if current_minute > 0 else 0
        
        if shots_per_minute > 0.3:
            return 'Экстра высокая', f'Шквал атак! {stats.total_shots} ударов'
        elif shots_per_minute > 0.2:
            return 'Очень высокая', f'Активный футбол, {stats.total_shots} ударов'
        elif shots_per_minute > 0.15:
            return 'Высокая', 'Команды много атакуют'
        elif shots_per_minute > 0.1:
            return 'Средняя', 'Умеренная активность'
        elif shots_per_minute > 0.05:
            return 'Низкая', 'Мало опасных моментов'
        else:
            return 'Очень низкая', 'Скучный матч'
    
    async def _find_next_goal_signal(self, stats: LiveStats, current_minute: int,
                                     current_goals: int, match: Match,
                                     league_factor: float = 1.0,
                                     team_factor: float = 1.0,
                                     xg_data: Optional[Dict] = None) -> Optional[GoalSignal]:
        if current_minute < self.params['min_minutes_for_analysis']:
            return None
        
        signals = []
        
        for interval in self.analysis_intervals:
            if interval <= current_minute:
                continue
            
            minutes_left = interval - current_minute
            
            base_probability = await self._calculate_goal_probability(
                stats, current_minute, minutes_left, current_goals, xg_data
            )
            
            adjusted_probability = base_probability * league_factor * team_factor
            threshold = self.thresholds.get(interval, 0.5)
            
            # Проверяем достаточно ли данных
            if current_minute < 10 and stats.total_shots < 2:
                continue
            
            if adjusted_probability < threshold:
                continue
            
            if not self._validate_signal(stats, current_minute, interval, 
                                         adjusted_probability, xg_data):
                continue
            
            if match and self._is_duplicate_signal(match, interval):
                continue
            
            signal_type = 'HIGH' if adjusted_probability >= self.params['high_probability_threshold'] else 'NORMAL'
            
            description = self._generate_signal_description(
                adjusted_probability, minutes_left, interval, stats, xg_data
            )
            
            signal = GoalSignal(
                match_id=match.id,
                predicted_minute=interval,
                probability=adjusted_probability * 100,
                signal_type=signal_type,
                description=description,
                timestamp=datetime.now(),
                stats=stats.to_dict(),
                minutes_left=minutes_left,
                xg_data=xg_data
            )
            signals.append(signal)
        
        if signals:
            valid_signals = [s for s in signals if s.probability > 30 and s.predicted_minute <= 90]
            if valid_signals:
                if xg_data and xg_data.get('total_xg', 0) > 0:
                    return max(valid_signals, 
                              key=lambda x: x.probability * (1 + xg_data.get('total_xg', 0) * 0.1))
                return max(valid_signals, key=lambda x: x.probability)
        return None
    
    def _is_duplicate_signal(self, match: Match, target_minute: int) -> bool:
        team_key = f"{match.home_team.id}_{match.away_team.id}"
        
        if target_minute <= 45:
            time_range = "first_half"
        elif target_minute <= 60:
            time_range = "early_second"
        elif target_minute <= 75:
            time_range = "mid_second"
        else:
            time_range = "late_second"
        
        signal_id = f"{team_key}_{time_range}"
        
        if signal_id in self.cache['team_signals'][team_key]:
            return True
        
        self.cache['team_signals'][team_key].add(time_range)
        return False
    
    async def _calculate_goal_probability(self, stats: LiveStats, current_minute: int,
                                     minutes_left: int, current_goals: int,
                                     xg_data: Optional[Dict] = None) -> float:
    """Рассчитывает вероятность гола с использованием xG"""
    if minutes_left <= 0:
        return 0
    
    if current_minute < self.params['min_minutes_for_analysis']:
        return 0.3
    
    factors = []
    total_weight = 0
    
    # 1. xG фактор (самый важный)
    if xg_data and self.params['use_xg'] and xg_data.get('total_xg', 0) > 0:
        total_xg = xg_data.get('total_xg', 0)
        
        # Учитываем уже забитые голы
        remaining_xg = max(0, total_xg - current_goals)
        
        # Прогнозируем xG на оставшееся время
        time_ratio = minutes_left / 90
        expected_xg = remaining_xg * time_ratio
        
        # Нормализуем (1.2 xG = 1 гол)
        xg_factor = min(1.0, expected_xg / self.params['xg_per_goal'])
        
        # xG имеет больший вес в начале матча
        time_weight = 1.0 - (current_minute / 90) * 0.3
        adjusted_weight = self.weights['xg'] * time_weight
        
        factors.append(xg_factor * adjusted_weight)
        total_weight += adjusted_weight
        
        logger.debug(f"xG фактор: {xg_factor:.3f} (remaining={remaining_xg:.2f}, expected={expected_xg:.2f})")
    
    # 2. Статистические факторы
    if current_minute > 0:
        # Удары в створ
        if stats.total_shots_ontarget > 0:
            ontarget_per_minute = stats.total_shots_ontarget / current_minute
            expected_ontarget = ontarget_per_minute * minutes_left
            ontarget_factor = min(1.0, expected_ontarget / self.params['ontarget_per_goal'])
            factors.append(ontarget_factor * self.weights['shots_ontarget'])
            total_weight += self.weights['shots_ontarget']
        
        # Опасные атаки
        if stats.total_dangerous_attacks > 0:
            dangerous_per_minute = stats.total_dangerous_attacks / current_minute
            expected_dangerous = dangerous_per_minute * minutes_left
            dangerous_factor = min(1.0, expected_dangerous / self.params['dangerous_attack_per_goal'])
            factors.append(dangerous_factor * self.weights['dangerous_attacks'])
            total_weight += self.weights['dangerous_attacks']
        
        # Общие удары
        if stats.total_shots > 0:
            shots_per_minute = stats.total_shots / current_minute
            expected_shots = shots_per_minute * minutes_left
            shots_factor = min(1.0, expected_shots / self.params['shots_per_goal'])
            factors.append(shots_factor * self.weights['shots'])
            total_weight += self.weights['shots']
    
    if total_weight > 0:
        probability = sum(factors)
    else:
        probability = 0.3
    
    # Корректировка на голы
    if current_goals > 0:
        probability *= (1 + current_goals * 0.1)
    
    # Время матча
    time_factor = minutes_left / 45
    probability *= min(1.0, time_factor * 1.3)
    
    return max(0.3, min(self.params['max_confidence'], probability))
    
    def _validate_signal(self, stats: LiveStats, current_minute: int,
                        target_minute: int, probability: float,
                        xg_data: Optional[Dict] = None) -> bool:
        if xg_data and xg_data.get('total_xg', 0) < 0.5:
            return False
        
        if current_minute < 30 and stats.total_shots < 4:
            return False
        
        if target_minute >= 75 and stats.total_shots < 8:
            return False
        
        if target_minute > 90:
            return False
        
        return True
    
    def _generate_signal_description(self, probability: float, minutes_left: int,
                                    target_minute: int, stats: LiveStats,
                                    xg_data: Optional[Dict] = None) -> str:
        if probability >= 0.8:
            base = "🚨 КРИТИЧЕСКИ ВЫСОКАЯ"
        elif probability >= 0.7:
            base = "⚡ ЭКСТРА ВЫСОКАЯ"
        elif probability >= 0.6:
            base = "🔥 ОЧЕНЬ ВЫСОКАЯ"
        elif probability >= 0.5:
            base = "📊 ХОРОШАЯ"
        else:
            base = "📈 ПОВЫШЕННАЯ"
        
        xg_part = f" (xG={xg_data['total_xg']:.2f})" if xg_data and xg_data.get('total_xg', 0) > 0.5 else ""
        shots_part = f", {stats.total_shots_ontarget} в створ" if stats.total_shots_ontarget > 3 else ""
        
        return f"{base} вероятность гола к {target_minute}'{xg_part}{shots_part}"
    
    def _calculate_attack_potential(self, stats: LiveStats, current_minute: int,
                               xg_data: Optional[Dict] = None) -> str:
    """Определяет атакующий потенциал с учетом xG"""
    if current_minute < 5:
        return "⚖️ Разведка"
    
    # Если есть xG, используем его
    if xg_data and xg_data.get('total_xg', 0) > 0:
        total_xg = xg_data['total_xg']
        xg_per_minute = total_xg / max(1, current_minute)
        
        if total_xg > 2.5:
            return "🔥🔥🔥🔥🔥 РАЗГРОМНЫЙ"
        elif total_xg > 2.0:
            return "🔥🔥🔥🔥 ОЧЕНЬ ВЫСОКИЙ"
        elif total_xg > 1.5:
            return "🔥🔥🔥 ВЫСОКИЙ"
        elif total_xg > 1.0:
            return "🔥🔥 СРЕДНИЙ"
        elif total_xg > 0.5:
            return "🔥 НИЗКИЙ"
        else:
            return "💧 ОЧЕНЬ НИЗКИЙ"
    
    # Если xG нет, используем статистику ударов
    shots_per_minute = stats.total_shots / current_minute
    
    if shots_per_minute > 0.25:
        return "🔥🔥🔥🔥 РАЗГРОМНЫЙ"
    elif shots_per_minute > 0.2:
        return "🔥🔥🔥 ОЧЕНЬ ВЫСОКИЙ"
    elif shots_per_minute > 0.15:
        return "🔥🔥 ВЫСОКИЙ"
    elif shots_per_minute > 0.1:
        return "🔥 СРЕДНИЙ"
    elif shots_per_minute > 0.05:
        return "💧 НИЗКИЙ"
    else:
        return "💧💧 ОЧЕНЬ НИЗКИЙ"
    
    def confirm_goal(self, match_id: int, signal_minute: int, actual_minute: int,
                    signal_probability: float = None,
                    xg_data: Optional[Dict] = None) -> Dict:
        with self.history_lock:
            result = {
                'was_correct': False,
                'time_error': abs(signal_minute - actual_minute),
                'signal_found': False,
                'match_id': match_id,
                'actual_minute': actual_minute,
                'signal_minute': signal_minute
            }
            
            for signal in self.signals_history:
                if (signal.get('match_id') == match_id and 
                    signal.get('signal_minute') == signal_minute):
                    signal['actual_goal_minute'] = actual_minute
                    signal['time_error'] = result['time_error']
                    signal['was_correct'] = result['time_error'] <= 10
                    signal['confirmed_at'] = datetime.now().isoformat()
                    result['signal_found'] = True
                    result['was_correct'] = signal['was_correct']
                    break
            
            if result['signal_found']:
                time_key = self._get_time_key(signal_minute)
                self.accuracy_stats['signals_by_time'][time_key]['total'] += 1
                if result['was_correct']:
                    self.accuracy_stats['signals_by_time'][time_key]['correct'] += 1
                
                self._learn_from_result(signal_minute, result['time_error'],
                                       signal_probability, result['was_correct'],
                                       xg_data)
            
            self.accuracy_stats['goals_actual'] += 1
            self.schedule_save()
        
        return result
    
    def _get_time_key(self, minute: int) -> int:
        for t in self.CRITICAL_TIMES:
            if minute <= t:
                return t
        return 90
    
    def _learn_from_result(self, predicted_minute: int, time_error: int,
                          probability: float, was_correct: bool,
                          xg_data: Optional[Dict] = None):
        if was_correct:
            self.thresholds[predicted_minute] *= 0.98
        else:
            self.thresholds[predicted_minute] *= 1.02
        
        for t in self.thresholds:
            self.thresholds[t] = max(0.3, min(0.8, self.thresholds[t]))
        
        if probability:
            error_ratio = time_error / 45
            learning_rate = self.params['learning_rate']
            
            for key in self.weights:
                if was_correct:
                    if key == 'xg' and xg_data:
                        self.weights[key] *= (1 + learning_rate * 1.5 * (1 - error_ratio))
                    else:
                        self.weights[key] *= (1 + learning_rate * (1 - error_ratio))
                else:
                    self.weights[key] *= (1 - learning_rate * error_ratio)
            
            total = sum(self.weights.values())
            if total > 0:
                for key in self.weights:
                    self.weights[key] /= total
        
        if xg_data and was_correct:
            self.accuracy_stats['xg_accuracy'] = (
                self.accuracy_stats.get('xg_accuracy', 0) * 0.95 + 
                (1 if xg_data.get('total_xg', 0) > 0.5 else 0) * 0.05
            )
    
    def save_signal_to_history(self, match: Match, signal: GoalSignal):
        with self.history_lock:
            for s in self.signals_history:
                if (s.get('match_id') == match.id and 
                    s.get('signal_minute') == signal.predicted_minute):
                    return
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'match_id': match.id,
                'home_team': match.home_team.name,
                'home_id': match.home_team.id,
                'away_team': match.away_team.name,
                'away_id': match.away_team.id,
                'league_id': match.league_id,
                'league_name': match.league_name,
                'signal_minute': signal.predicted_minute,
                'signal_probability': signal.probability,
                'match_minute': match.minute,
                'score': match.score,
                'shots_total': signal.stats.get('shots', {}).get('total', 0) if signal.stats else 0,
                'shots_ontarget': signal.stats.get('shots', {}).get('ontarget_total', 0) if signal.stats else 0,
                'xg_total': signal.xg_data.get('total_xg') if signal.xg_data else None,
                'xg_home': signal.xg_data.get('home_xg') if signal.xg_data else None,
                'xg_away': signal.xg_data.get('away_xg') if signal.xg_data else None
            }
            
            self.signals_history.append(entry)
            logger.info(f"💾 Сигнал {len(self.signals_history)}: {match.home_team.name}-{match.away_team.name} "
                       f"~{signal.predicted_minute}' ({signal.probability:.1f}%)")
            
            self.accuracy_stats['total_signals'] = len(self.signals_history)
            self.accuracy_stats['goals_predicted'] = len(self.signals_history)
            self.schedule_save()
    
    def schedule_save(self):
        self.save_queue.append(time.time())
        if time.time() - self.last_save_time > self.save_interval:
            self._save_all()
    
    def start_auto_save(self):
        def auto_saver():
            while True:
                time.sleep(30)
                self._save_all()
        thread = threading.Thread(target=auto_saver, daemon=True)
        thread.start()
    
    def _save_all(self):
        try:
            with self.history_lock:
                self._save_stats()
                self._save_signals()
                self._save_weights()
                self._save_thresholds()
                self._save_xg_stats()
                self.last_save_time = time.time()
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    
    def _save_stats(self):
        try:
            stats_to_save = {
                'stats': dict(self.accuracy_stats),
                'params': self.params,
                'last_updated': datetime.now().isoformat()
            }
            if 'league_stats' in stats_to_save['stats']:
                stats_to_save['stats']['league_stats'] = dict(stats_to_save['stats']['league_stats'])
            if 'team_stats' in stats_to_save['stats']:
                stats_to_save['stats']['team_stats'] = dict(stats_to_save['stats']['team_stats'])
            
            with open('signal_accuracy.json', 'w', encoding='utf-8') as f:
                json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")
    
    def _save_weights(self):
        try:
            with open('model_weights.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'weights': self.weights,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения весов: {e}")
    
    def _save_thresholds(self):
        try:
            with open('model_thresholds.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'thresholds': self.thresholds,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения порогов: {e}")
    
    def _save_signals(self):
        try:
            recent = self.signals_history[-200:]
            with open('signals_history_latest.json', 'w', encoding='utf-8') as f:
                json.dump(recent, f, ensure_ascii=False, indent=2)
            
            if recent:
                csv_filename = f'signals_history_{datetime.now().strftime("%Y%m%d")}.csv'
                with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
                    fieldnames = ['timestamp', 'match_id', 'home_team', 'away_team', 
                                 'signal_minute', 'signal_probability', 'match_minute', 
                                 'score', 'xg_total']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for s in recent:
                        row = {k: s.get(k) for k in fieldnames if k in s}
                        writer.writerow(row)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {e}")
    
    def _save_xg_stats(self):
        try:
            xg_stats = {
                'xg_accuracy': self.accuracy_stats.get('xg_accuracy', 0),
                'xg_per_goal': self.params['xg_per_goal'],
                'xg_weight': self.weights['xg'],
                'xg_requests': self.xg_manager.get_stats() if hasattr(self.xg_manager, 'get_stats') else {},
                'last_updated': datetime.now().isoformat()
            }
            with open('xg_stats.json', 'w', encoding='utf-8') as f:
                json.dump(xg_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения xG статистики: {e}")
    
    def clear_cache(self):
        self.cache['match_analysis'].clear()
        self.cache['match_xg'].clear()
        self.cache['team_signals'].clear()
        logger.debug("🧹 Кэш очищен")
    
    async def close(self):
        await self.xg_manager.close()