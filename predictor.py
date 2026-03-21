import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional, Any
from collections import defaultdict
import json
import os
import random
import traceback
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

import config
from models import Match
from team_form import TeamFormAnalyzer
from statistical_models import StatisticalModels, MonteCarloSimulator
from feature_engineering import AdvancedFeatureEngineer
from match_analyzer import MatchAnalyzer, MatchFilter
from signal_validator import SignalValidator

logger = logging.getLogger(__name__)

class Predictor:
    def __init__(self, model_path: str = 'data/models/xgboost_model.pkl'):
        self.min_signal_probability = getattr(config, 'MIN_PROBABILITY_FOR_SIGNAL', 0.48)
        logger.info(f"Минимальная вероятность для сигнала: {self.min_signal_probability*100:.0f}%")
        
        self.weights = {
            'xg': 0.28, 'shots_ontarget': 0.18, 'team_form': 0.15,
            'dangerous_attacks': 0.12, 'shots': 0.10, 'corners': 0.09,
            'possession': 0.05, 'h2h': 0.03
        }
        
        self.thresholds = {'low': 0.15, 'medium': 0.25, 'high': 0.40, 'very_high': 0.55}
        
        self.predictions_history = []
        self.max_history_size = 1000
        
        self.accuracy_stats = {
            'total_predictions': 0, 'total_signals': 0, 'signals_sent_46plus': 0,
            'signals_filtered_out': 0, 'correct_predictions': 0, 'incorrect_predictions': 0,
            'accuracy_rate': 0.0, 'calibration_data': [], 'feature_importance': {},
            'by_confidence': {'VERY_HIGH': {'total': 0, 'correct': 0}, 'HIGH': {'total': 0, 'correct': 0},
                            'MEDIUM': {'total': 0, 'correct': 0}, 'LOW': {'total': 0, 'correct': 0},
                            'VERY_LOW': {'total': 0, 'correct': 0}},
            'by_minute': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'by_league': defaultdict(lambda: {'total': 0, 'correct': 0}),
            'last_updated': datetime.now().isoformat()
        }
        
        self.team_analyzer = TeamFormAnalyzer()
        self.stat_models = StatisticalModels()
        self.monte_carlo = MonteCarloSimulator(n_simulations=10000)
        self.feature_engineer = AdvancedFeatureEngineer()
        self.match_analyzer = MatchAnalyzer()
        self.match_filter = MatchFilter()
        self.signal_validator = SignalValidator()
        
        self.league_levels = self._init_league_levels()
        self.learning_rate = 0.01
        self.min_matches_for_update = 50
        self.model_path = model_path
        
        self.xgb_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self._init_xgb_model()
        
        self.half_goals = {}
        self.match_last_signal = {}
        self.match_signal_count = {}
        self.max_signals_per_match = 3
        self.min_time_between_signals = 600
        
        self.league_averages = defaultdict(lambda: {
            'shots': 10, 'shots_on_target': 3.5, 'xg': 1.2, 'corners': 4.5,
            'possession': 50, 'dangerous_attacks': 20, 'passes': 400, 'fouls': 12, 'yellow_cards': 2
        })
        
        logger.info("Predictor (XGBoost) инициализирован")
    
    def _init_xgb_model(self):
        try:
            if os.path.exists(self.model_path):
                self.xgb_model = joblib.load(self.model_path)
                logger.info(f"Загружена XGBoost модель из {self.model_path}")
            else:
                self.xgb_model = xgb.XGBClassifier(
                    n_estimators=200, max_depth=5, learning_rate=0.03,
                    reg_alpha=2.0, reg_lambda=3.0, subsample=0.8,
                    colsample_bytree=0.8, colsample_bylevel=0.7, gamma=0.5,
                    min_child_weight=3, scale_pos_weight=1.2, random_state=42,
                    eval_metric='logloss', use_label_encoder=False
                )
                logger.info("Создана новая XGBoost модель")
        except Exception as e:
            logger.error(f"Ошибка XGBoost: {e}")
            self.xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=3, random_state=42)
    
    def _init_league_levels(self) -> Dict:
        top_leagues = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2}
        return defaultdict(lambda: 2, top_leagues)
    
    def predict_match(self, match: Match) -> Dict:
        try:
            home_stats = self._extract_team_stats(match, is_home=True)
            away_stats = self._extract_team_stats(match, is_home=False)
            
            home_form = None
            away_form = None
            if match.home_team and hasattr(match.home_team, 'id'):
                home_form = self.team_analyzer.get_team_form(match.home_team.id)
            if match.away_team and hasattr(match.away_team, 'id'):
                away_form = self.team_analyzer.get_team_form(match.away_team.id)
            
            h2h_data = None
            if match.home_team and match.away_team:
                h2h_data = self.team_analyzer.get_head_to_head(
                    match.home_team.id, match.away_team.id, limit=5
                )
            
            base_prob = 0.35
            
            minute = match.minute or 0
            if minute > 75:
                base_prob += 0.15
            elif minute > 60:
                base_prob += 0.10
            elif minute > 45:
                base_prob += 0.05
            
            home_score = match.home_score or 0
            away_score = match.away_score or 0
            if home_score == away_score:
                base_prob += 0.05
            if home_score + away_score < 2:
                base_prob += 0.05
            
            if home_stats.get('shots', 0) + away_stats.get('shots', 0) > 15:
                base_prob += 0.05
            
            if home_form:
                base_prob += (home_form.get('weighted_form', 0.5) - 0.5) * 0.1
            if away_form:
                base_prob += (away_form.get('weighted_form', 0.5) - 0.5) * 0.1
            
            goal_probability = min(0.85, max(0.25, base_prob))
            
            if goal_probability >= 0.55:
                confidence_level = "VERY_HIGH"
            elif goal_probability >= 0.50:
                confidence_level = "HIGH"
            elif goal_probability >= 0.45:
                confidence_level = "MEDIUM"
            elif goal_probability >= 0.35:
                confidence_level = "LOW"
            else:
                confidence_level = "VERY_LOW"
            
            signal = None
            if goal_probability >= self.min_signal_probability:
                signal = self._generate_signal(match, goal_probability, confidence_level, home_stats, away_stats)
            
            result = {
                'match_id': match.id,
                'match': match,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'goal_probability': round(goal_probability, 3),
                'confidence_level': confidence_level,
                'signal': signal,
                'home_stats': home_stats,
                'away_stats': away_stats,
                'minute': match.minute,
                'timestamp': datetime.now().isoformat()
            }
            
            self._add_to_history(result)
            # СОХРАНЯЕМ ПОСЛЕ КАЖДОГО ПРОГНОЗА
            self.save_predictions()
            return result
            
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return self._get_default_prediction(match)
    
    def _generate_signal(self, match: Match, goal_prob: float, confidence: str,
                        home_stats: Dict, away_stats: Dict) -> Dict:
        from translations import get_country_info, get_league_icon
        
        confidence_emojis = {"VERY_HIGH": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "VERY_LOW": "⚪"}
        confidence_text = {"VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ", "HIGH": "ВЫСОКАЯ", "MEDIUM": "СРЕДНЯЯ", "LOW": "НИЗКАЯ", "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"}
        
        emoji = confidence_emojis.get(confidence, "⚪")
        conf_text = confidence_text.get(confidence, confidence)
        
        home_name = match.home_team.name if match.home_team else "Хозяева"
        away_name = match.away_team.name if match.away_team else "Гости"
        
        country_info = {'flag': '🌍', 'name': ''}
        if match.home_team and match.home_team.country_code:
            country_info = get_country_info(match.home_team.country_code)
        elif match.away_team and match.away_team.country_code:
            country_info = get_country_info(match.away_team.country_code)
        
        league_icon = get_league_icon(match.league_name) if match.league_name else '🏆'
        league_display = match.league_name if match.league_name else ""
        
        location_parts = []
        if country_info['name']:
            location_parts.append(f"{country_info['flag']} {country_info['name']}")
        if league_display:
            location_parts.append(f"{league_icon} {league_display}")
        
        location_str = f" | {' | '.join(location_parts)}" if location_parts else ""
        
        current_score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        period = ""
        if match.minute:
            if match.minute < 45:
                period = "1-й тайм"
            elif match.minute < 90:
                period = "2-й тайм"
            else:
                period = "Доп. время"
        
        has_stats = any([
            home_stats.get('shots', 0) > 0,
            away_stats.get('shots', 0) > 0,
            home_stats.get('shots_on_target', 0) > 0,
            away_stats.get('shots_on_target', 0) > 0
        ])
        
        message_lines = [
            f"{emoji} ⚽ ПОТЕНЦИАЛЬНЫЙ ГОЛ!",
            "━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"🏟 {home_name}  vs  {away_name}{location_str}",
            f"📊 Счет: {current_score}",
            f"⏱ Минута: {match.minute or 0}' {period}",
            "",
            f"📈 Вероятность гола: {goal_prob*100:.1f}%",
            f"🎯 Уверенность: {conf_text}",
        ]
        
        if has_stats:
            home_shots = home_stats.get('shots', 0)
            away_shots = away_stats.get('shots', 0)
            home_shots_ontarget = home_stats.get('shots_on_target', 0)
            away_shots_ontarget = away_stats.get('shots_on_target', 0)
            home_xg = home_stats.get('xg', 0.5)
            away_xg = away_stats.get('xg', 0.5)
            home_possession = home_stats.get('possession', 50)
            away_possession = away_stats.get('possession', 50)
            home_corners = home_stats.get('corners', 0)
            away_corners = away_stats.get('corners', 0)
            
            message_lines.extend([
                "",
                "📊 СТАТИСТИКА:",
                f"  • Удары: {home_shots} : {away_shots}",
                f"  • В створ: {home_shots_ontarget} : {away_shots_ontarget}",
                f"  • xG: {home_xg:.2f} : {away_xg:.2f}",
                f"  • Владение: {home_possession:.0f}% : {away_possession:.0f}%",
                f"  • Угловые: {home_corners} : {away_corners}",
            ])
        
        signal = {
            'emoji': emoji,
            'message': "\n".join(message_lines),
            'confidence': confidence,
            'probability': goal_prob,
            'match_id': match.id,
            'current_score': current_score,
            'timestamp': datetime.now()
        }
        
        return signal
    
    def analyze_live_match(self, match: Match) -> Optional[Dict]:
        try:
            if match.id in self.match_signal_count and self.match_signal_count[match.id] >= self.max_signals_per_match:
                return None
            if match.id in self.match_last_signal:
                if (datetime.now() - self.match_last_signal[match.id]).total_seconds() < self.min_time_between_signals:
                    return None
            
            if not self._should_analyze_match(match):
                return None
            
            prediction = self.predict_match(match)
            prob = prediction.get('goal_probability', 0)
            conf = prediction.get('confidence_level', 'MEDIUM')
            
            if prob >= self.min_signal_probability:
                should_send = False
                if conf in ['VERY_HIGH', 'HIGH']:
                    should_send = True
                elif conf == 'MEDIUM' and prob >= 0.50:
                    should_send = True
                elif conf == 'LOW' and prob >= 0.55:
                    should_send = True
                
                if should_send:
                    half = "1-й тайм" if match.minute and match.minute < 45 else "2-й тайм"
                    self.match_last_signal[match.id] = datetime.now()
                    self.match_signal_count[match.id] = self.match_signal_count.get(match.id, 0) + 1
                    self.accuracy_stats['signals_sent_46plus'] += 1
                    logger.info(f"СИГНАЛ ОТПРАВЛЕН! Матч {match.id} ({half}) - {prob*100:.1f}% ({conf})")
                    # СОХРАНЯЕМ ПОСЛЕ СИГНАЛА
                    self.save_predictions()
                    return prediction.get('signal')
            
            return None
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return None
    
    def _should_analyze_match(self, match: Match) -> bool:
        if match.minute and match.minute > 75:
            return False
        if abs((match.home_score or 0) - (match.away_score or 0)) >= 3:
            return False
        if (match.home_score or 0) >= 4 or (match.away_score or 0) >= 4:
            return False
        if match.minute and match.minute < 10:
            return False
        if match.minute and 85 <= match.minute <= 90:
            return False
        return True
    
    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        stats = {
            'shots': 0,
            'shots_on_target': 0,
            'possession': 50,
            'xg': 0.5,
            'corners': 0,
            'has_real_stats': False
        }
        
        if not match.stats or not isinstance(match.stats, dict):
            return stats
        
        prefix = 'home' if is_home else 'away'
        
        stats['shots'] = match.stats.get(f'shots_{prefix}', 0)
        stats['shots_on_target'] = match.stats.get(f'shots_ontarget_{prefix}', 0)
        stats['possession'] = match.stats.get(f'possession_{prefix}', 50)
        stats['xg'] = match.stats.get(f'xg_{prefix}', 0.5)
        stats['corners'] = match.stats.get(f'corners_{prefix}', 0)
        
        if stats['shots'] > 0 or stats['shots_on_target'] > 0 or stats['xg'] != 0.5:
            stats['has_real_stats'] = True
        
        return stats
    
    def _add_to_history(self, prediction: Dict):
        self.predictions_history.append(prediction)
        if len(self.predictions_history) > self.max_history_size:
            self.predictions_history = self.predictions_history[-self.max_history_size:]
    
    def _get_default_prediction(self, match: Match) -> Dict:
        return {
            'match_id': match.id, 'match': match,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'goal_probability': 0.3, 'confidence_level': 'LOW', 'signal': None,
            'home_stats': {}, 'away_stats': {}, 'error': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_predictions(self, filename: str = 'data/predictions/predictions.json'):
        try:
            # Создаем папку если нужно
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Загружаем существующие предсказания если есть
            existing_predictions = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_predictions = existing_data.get('predictions', [])
                except:
                    pass
            
            # Объединяем с новыми (избегаем дубликатов по match_id и timestamp)
            all_predictions = existing_predictions.copy()
            new_ids = set(p.get('match_id', 0) for p in existing_predictions)
            
            for p in self.predictions_history[-100:]:
                match_id = p.get('match_id', 0)
                timestamp = p.get('timestamp', '')
                key = f"{match_id}_{timestamp[:19]}"
                
                # Проверяем, нет ли уже такого предсказания
                exists = False
                for ep in existing_predictions:
                    if ep.get('match_id') == match_id and ep.get('timestamp', '')[:19] == timestamp[:19]:
                        exists = True
                        break
                
                if not exists:
                    p_copy = {k: v for k, v in p.items() if k != 'match'}
                    all_predictions.append(p_copy)
            
            # Сортируем по времени
            all_predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Обновляем статистику
            correct = sum(1 for p in all_predictions if p.get('was_correct', False))
            total = len(all_predictions)
            self.accuracy_stats['total_predictions'] = total
            self.accuracy_stats['correct_predictions'] = correct
            self.accuracy_stats['incorrect_predictions'] = total - correct
            self.accuracy_stats['accuracy_rate'] = correct / total if total > 0 else 0
            
            # Сохраняем
            data = {
                'predictions': all_predictions,
                'accuracy_stats': self.accuracy_stats,
                'thresholds': self.thresholds,
                'half_goals': dict(self.half_goals),
                'match_signal_count': dict(self.match_signal_count),
                'min_signal_probability': self.min_signal_probability
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Сохранено {len(all_predictions)} предсказаний в {filename}")
            
            # Сохраняем XGBoost модель
            if self.xgb_model and hasattr(self.xgb_model, 'get_booster'):
                try:
                    _ = self.xgb_model.get_booster()
                    joblib.dump(self.xgb_model, self.model_path)
                    if self.feature_names:
                        with open(self.model_path.replace('.pkl', '_features.json'), 'w', encoding='utf-8') as f:
                            json.dump(self.feature_names, f)
                except Exception as e:
                    logger.error(f"Ошибка сохранения XGBoost: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    
    def load_predictions(self, filename: str = 'data/predictions/predictions.json'):
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.predictions_history = data.get('predictions', [])
                self.accuracy_stats.update(data.get('accuracy_stats', {}))
                self.thresholds.update(data.get('thresholds', self.thresholds))
                self.half_goals = data.get('half_goals', {})
                self.match_signal_count = data.get('match_signal_count', {})
                self.min_signal_probability = data.get('min_signal_probability', self.min_signal_probability)
                logger.info(f"Загружено {len(self.predictions_history)} предсказаний")
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
    
    def get_statistics(self) -> Dict:
        if not self.predictions_history:
            return {'total_predictions': 0, 'avg_probability': 0, 'signals_sent': self.accuracy_stats['total_signals'],
                    'signals_sent_46plus': self.accuracy_stats.get('signals_sent_46plus', 0),
                    'signals_filtered_out': self.accuracy_stats.get('signals_filtered_out', 0),
                    'accuracy_rate': self.accuracy_stats['accuracy_rate'],
                    'feature_importance': self.accuracy_stats['feature_importance'],
                    'by_confidence': self.accuracy_stats['by_confidence']}
        
        probs = [p.get('goal_probability', 0) for p in self.predictions_history]
        return {
            'total_predictions': len(self.predictions_history),
            'avg_probability': np.mean(probs),
            'signals_sent': self.accuracy_stats['total_signals'],
            'signals_sent_46plus': self.accuracy_stats.get('signals_sent_46plus', 0),
            'signals_filtered_out': self.accuracy_stats.get('signals_filtered_out', 0),
            'accuracy_rate': self.accuracy_stats['accuracy_rate'],
            'feature_importance': self.accuracy_stats['feature_importance'],
            'by_confidence': self.accuracy_stats['by_confidence']
        }