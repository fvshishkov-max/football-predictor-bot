import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

from models import Match, LiveStats
from team_form import TeamFormAnalyzer

logger = logging.getLogger(__name__)

class Predictor:
    """
    Класс для прогнозирования голов в футбольных матчах на основе статистики.
    Использует взвешенный подход с учетом xG, ударов, формы команд и других метрик.
    """
    
    def __init__(self, model_path: str = 'data/ml_model.pkl'):
        # Веса для различных факторов при расчете вероятности гола
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
        
        self.thresholds = {
            'low': 0.15,
            'medium': 0.25,
            'high': 0.35,
            'very_high': 0.45
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
            'last_updated': datetime.now().isoformat()
        }
        
        self.team_analyzer = TeamFormAnalyzer()
        self.league_levels = self._init_league_levels()
        self.learning_rate = 0.01
        self.min_matches_for_update = 50
        self.model_path = model_path
        self.ml_model = None
        self.scaler = StandardScaler()
        self._init_ml_model()
        self._last_factors_contributions = {}
        
        logger.info("Predictor инициализирован с весами: %s", self.weights)
    
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
    
    def predict_match(self, match: Match) -> Dict:
        """Основной метод для предсказания вероятности голов в матче"""
        try:
            home_stats = self._extract_team_stats(match, is_home=True)
            away_stats = self._extract_team_stats(match, is_home=False)
            
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
            
            home_goal_prob = self._calibrate_probability(home_goal_prob)
            away_goal_prob = self._calibrate_probability(away_goal_prob)
            total_goal_prob = self._calculate_total_goal_probability(home_goal_prob, away_goal_prob)
            confidence_level = self._determine_confidence_level(total_goal_prob)
            signal = self._generate_signal(match, home_goal_prob, away_goal_prob, total_goal_prob, confidence_level)
            
            result = {
                'match_id': match.id,
                'match': match,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
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
                'timestamp': datetime.now().isoformat()
            }
            
            self._add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при предсказании матча {match.id}: {e}")
            return self._get_default_prediction(match)
    
    def _get_h2h_factor(self, match: Match) -> Dict:
        """Анализирует историю личных встреч"""
        if not match.home_team or not match.away_team:
            return {'home': 1.0, 'away': 1.0}
        
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
    
    def _get_league_factor(self, match: Match) -> float:
        """Возвращает фактор силы лиги"""
        if not match.league_id:
            return 1.0
        
        level = self.league_levels[match.league_id]
        
        if level == 1:
            return 1.1
        else:
            return 0.95
    
    def _get_performance_vs_top(self, team_id: int) -> float:
        """Анализирует выступления против топ-команд"""
        stats = self.team_analyzer.get_team_performance_vs_top_teams(team_id)
        
        if stats['matches_analyzed'] == 0:
            return 1.0
        
        if stats['points_per_game'] > 1.5:
            return 1.15
        elif stats['points_per_game'] < 0.8:
            return 0.85
        else:
            return 1.0
    
    def _calculate_goal_probability(self, stats: Dict, is_home: bool = True, 
                                   team_form: Optional[Dict] = None,
                                   h2h_factor: float = 1.0,
                                   league_factor: float = 1.0,
                                   top_teams_factor: float = 1.0) -> float:
        """Рассчитывает вероятность гола"""
        factors = []
        total_weight = 0
        factors_contributions = {}
        
        factor_mappings = [
            ('xg', 'xg', 0.3),
            ('shots_ontarget', 'shots_on_target', 0.2),
            ('dangerous_attacks', 'dangerous_attacks', 0.15),
            ('shots', 'shots', 0.1),
            ('corners', 'corners', 0.08),
            ('possession', 'possession', 0.05)
        ]
        
        for key, stat_key, base_weight in factor_mappings:
            if key in self.weights:
                weight = self.weights[key]
                stat_value = stats.get(stat_key, 0)
                
                if key == 'xg':
                    normalized = min(stat_value / 3.0, 1.0)
                elif key == 'shots_ontarget':
                    normalized = min(stat_value / 10.0, 1.0)
                elif key == 'dangerous_attacks':
                    normalized = min(stat_value / 50.0, 1.0)
                elif key == 'shots':
                    normalized = min(stat_value / 20.0, 1.0)
                elif key == 'corners':
                    normalized = min(stat_value / 10.0, 1.0)
                elif key == 'possession':
                    normalized = stat_value / 100.0
                else:
                    normalized = 0.5
                
                contribution = normalized * weight
                factors.append(contribution)
                total_weight += weight
                factors_contributions[key] = contribution
        
        if team_form and 'team_form' in self.weights:
            form_factor = team_form.get('weighted_form', team_form.get('form', 0.5))
            contribution = form_factor * self.weights['team_form']
            factors.append(contribution)
            total_weight += self.weights['team_form']
            factors_contributions['team_form'] = contribution
        
        if 'h2h' in self.weights:
            contribution = h2h_factor * self.weights['h2h']
            factors.append(contribution)
            total_weight += self.weights['h2h']
            factors_contributions['h2h'] = contribution
        
        if is_home:
            home_bonus = 0.05
            factors.append(home_bonus)
            total_weight += 0.05
            factors_contributions['home_advantage'] = home_bonus
        
        if total_weight > 0:
            probability = sum(factors) / total_weight
        else:
            probability = 0.3
        
        probability *= league_factor
        probability *= top_teams_factor
        
        self._last_factors_contributions = factors_contributions
        
        return max(0.05, min(0.95, probability))
    
    def _calibrate_probability(self, probability: float) -> float:
        """Калибрует вероятность на основе исторических данных"""
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
        """Рассчитывает общую вероятность гола"""
        total_prob = 1 - (1 - home_prob) * (1 - away_prob)
        
        if total_prob > 0.95:
            total_prob = 0.95
        elif total_prob < 0.3:
            total_prob = total_prob * 1.2
        
        return total_prob
    
    def _determine_confidence_level(self, probability: float) -> str:
        """Определяет уровень уверенности"""
        if probability >= self.thresholds['very_high']:
            return "VERY_HIGH"
        elif probability >= self.thresholds['high']:
            return "HIGH"
        elif probability >= self.thresholds['medium']:
            return "MEDIUM"
        elif probability >= self.thresholds['low']:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _generate_signal(self, match: Match, home_prob: float, away_prob: float, 
                        total_prob: float, confidence: str) -> Dict:
        """Генерирует сигнал для отправки в Telegram"""
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
        
        if home_prob > away_prob + 0.1:
            team_focus = f"⚽ {home_name}"
        elif away_prob > home_prob + 0.1:
            team_focus = f"⚽ {away_name}"
        else:
            team_focus = "⚽ Обе команды"
        
        message = (
            f"{emoji} Потенциальный гол!\n"
            f"{home_name} vs {away_name}\n\n"
            f"📊 Вероятность гола: {total_prob*100:.1f}%\n"
            f"🎯 Уверенность: {confidence}\n"
            f"👥 {team_focus}\n\n"
            f"🏠 {home_name}: {home_prob*100:.1f}%\n"
            f"✈️ {away_name}: {away_prob*100:.1f}%"
        )
        
        if match.minute:
            message += f"\n⏱ Минута: {match.minute}'"
        
        if match.start_time:
            message += f"\n⏱ Начало: {match.start_time.strftime('%H:%M')}"
        
        signal = {
            'emoji': emoji,
            'message': message,
            'confidence': confidence,
            'probability': total_prob,
            'home_prob': home_prob,
            'away_prob': away_prob,
            'match_id': match.id,
            'timestamp': datetime.now()
        }
        
        return signal
    
    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        """Извлекает статистику для команды"""
        stats = {
            'shots': 0,
            'shots_on_target': 0,
            'corners': 0,
            'possession': 50,
            'dangerous_attacks': 0,
            'xg': 0.5
        }
        
        if not match.stats:
            return stats
        
        team_id = match.home_team.id if is_home and match.home_team else None
        if not team_id and not is_home and match.away_team:
            team_id = match.away_team.id
        
        if not team_id:
            return stats
        
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
                            
                            if 'shots on target' in name or 'удары в створ' in name:
                                stats['shots_on_target'] = value
                            elif 'total shots' in name or 'всего ударов' in name:
                                stats['shots'] = value
                            elif 'corner kicks' in name or 'угловые' in name:
                                stats['corners'] = value
                            elif 'possession' in name or 'владение' in name:
                                stats['possession'] = value
                            elif 'dangerous attacks' in name or 'опасные атаки' in name:
                                stats['dangerous_attacks'] = value
                            elif 'xg' in name or 'expected goals' in name:
                                stats['xg'] = value
        
        return stats
    
    def _add_to_history(self, prediction: Dict):
        """Добавляет предсказание в историю"""
        self.predictions_history.append(prediction)
        
        if len(self.predictions_history) > self.max_history_size:
            self.predictions_history = self.predictions_history[-self.max_history_size:]
        
        if len(self.predictions_history) % 50 == 0:
            self._update_weights_gradient()
            self._update_weights_ml()
            self._optimize_thresholds()
    
    def _update_weights_gradient(self):
        """Обновляет веса градиентным спуском"""
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
        """Обновляет веса на основе ML модели"""
        try:
            if len(self.accuracy_stats['calibration_data']) < self.min_matches_for_update:
                return
            
            X = []
            y = []
            
            for pred in self.predictions_history[-500:]:
                if 'error' in pred and pred['error']:
                    continue
                
                match = pred.get('match')
                if not match:
                    continue
                
                features = self._extract_features(match, pred)
                X.append(features.flatten())
                
                if hasattr(match, 'total_goals'):
                    y.append(1 if match.total_goals > 0 else 0)
            
            if len(X) < self.min_matches_for_update:
                return
            
            X = np.array(X)
            y = np.array(y)
            X_scaled = self.scaler.fit_transform(X)
            self.ml_model.fit(X_scaled, y)
            
            if hasattr(self.ml_model, 'coef_'):
                feature_names = [
                    'home_prob', 'away_prob', 'total_prob',
                    'home_form', 'home_xg_for', 'home_xg_against',
                    'away_form', 'away_xg_for', 'away_xg_against',
                    'home_xg_current', 'away_xg_current',
                    'home_sot', 'away_sot',
                    'league_level', 'minute'
                ]
                
                importance = np.abs(self.ml_model.coef_[0])
                for name, imp in zip(feature_names, importance):
                    self.accuracy_stats['feature_importance'][name] = float(imp)
                
                logger.info(f"📊 Важность признаков: {self.accuracy_stats['feature_importance']}")
            
            joblib.dump(self.ml_model, self.model_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ML модели: {e}")
    
    def _optimize_thresholds(self):
        """Оптимизирует пороговые значения"""
        try:
            if len(self.accuracy_stats['calibration_data']) < 100:
                return
            
            recent_data = self.accuracy_stats['calibration_data'][-200:]
            best_thresholds = {}
            
            for level, default_threshold in [('low', 0.15), ('medium', 0.25), 
                                            ('high', 0.35), ('very_high', 0.45)]:
                best_acc = 0
                best_thresh = default_threshold
                
                for threshold in np.arange(0.1, 0.6, 0.05):
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
    
    def _extract_features(self, match: Match, prediction: Dict) -> np.ndarray:
        """Извлекает признаки для ML модели"""
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
    
    def analyze_live_match(self, match: Match) -> Optional[Dict]:
        """Анализирует live-матч и генерирует сигнал"""
        try:
            prediction = self.predict_match(match)
            
            if self._should_send_signal(prediction):
                logger.info(f"Сгенерирован сигнал для матча {match.id} с вероятностью {prediction['total_goal_probability']:.2f}")
                
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
            logger.error(f"Ошибка при анализе live-матча {match.id}: {e}")
            return None
    
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
    
    def update_accuracy(self, prediction_id: str, actual_goals: int):
        """Обновляет статистику точности"""
        try:
            for pred in self.predictions_history:
                if str(pred.get('match_id')) == str(prediction_id):
                    predicted_prob = pred.get('total_goal_probability', 0)
                    
                    had_goal = actual_goals > 0
                    predicted_goal = predicted_prob > 0.5
                    
                    self.accuracy_stats['total_predictions'] += 1
                    
                    self.accuracy_stats['calibration_data'].append(
                        (predicted_prob, 1 if had_goal else 0)
                    )
                    
                    if len(self.accuracy_stats['calibration_data']) > 1000:
                        self.accuracy_stats['calibration_data'] = \
                            self.accuracy_stats['calibration_data'][-1000:]
                    
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
        """Возвращает предсказание по умолчанию"""
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
        """Возвращает статистику точности"""
        return self.accuracy_stats.copy()
    
    def get_weights_history(self) -> List:
        """Возвращает историю весов"""
        return self.weights_history.copy()
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику работы"""
        if not self.predictions_history:
            return {
                'total_predictions': 0,
                'avg_probability': 0,
                'signals_sent': self.accuracy_stats['total_signals'],
                'confidence_distribution': {},
                'feature_importance': self.accuracy_stats['feature_importance'],
                'current_weights': self.weights
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
            'current_weights': self.weights
        }
    
    def save_predictions(self, filename: str = 'data/predictions.json'):
        """Сохраняет предсказания в файл"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            data = {
                'predictions': [],
                'weights_history': self.weights_history,
                'accuracy_stats': self.accuracy_stats
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
        """Загружает предсказания из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.predictions_history = data.get('predictions', [])
                self.weights_history = data.get('weights_history', [])
                self.accuracy_stats.update(data.get('accuracy_stats', {}))
                
                logger.info(f"Загружено {len(self.predictions_history)} предсказаний из {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки предсказаний: {e}")