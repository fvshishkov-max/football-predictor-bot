import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json
import os
import random
import traceback
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

# Импортируем config для получения настроек
import config
from models import Match
from team_form import TeamFormAnalyzer
from statistical_models import StatisticalModels, MonteCarloSimulator
from feature_engineering import AdvancedFeatureEngineer

logger = logging.getLogger(__name__)

class Predictor:
    """
    Улучшенный предиктор с XGBoost и продвинутым feature engineering
    Отправляет сигналы только при вероятности >= 46%
    """
    
    def __init__(self, model_path: str = 'data/xgboost_model.pkl'):
        # Минимальная вероятность для отправки сигнала (из config или по умолчанию 46%)
        self.min_signal_probability = getattr(config, 'MIN_PROBABILITY_FOR_SIGNAL', 0.46)
        logger.info(f"🎯 Минимальная вероятность для сигнала: {self.min_signal_probability*100:.0f}%")
        
        # Веса для legacy режима (если XGBoost недоступен)
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
        
        # Пороговые значения (будем калибровать под XGBoost)
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
            'signals_sent_46plus': 0,
            'signals_filtered_out': 0,
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
            'last_updated': datetime.now().isoformat()
        }
        
        self.team_analyzer = TeamFormAnalyzer()
        self.stat_models = StatisticalModels()
        self.monte_carlo = MonteCarloSimulator(n_simulations=10000)
        self.feature_engineer = AdvancedFeatureEngineer()
        
        self.league_levels = self._init_league_levels()
        self.learning_rate = 0.01
        self.min_matches_for_update = 50
        self.model_path = model_path
        
        # XGBoost модель
        self.xgb_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self._init_xgb_model()
        
        # Elo интеграция
        self.elo_predictor = None
        self.use_elo = True
        
        # Для отслеживания голов по таймам
        self.half_goals = {}
        self.half_signals = {}
        
        # Для контроля дублирования сигналов
        self.match_last_signal = {}
        self.match_signal_count = {}
        self.max_signals_per_match = 3
        self.min_time_between_signals = 600
        
        # Средние по лигам (будут заполняться по мере накопления данных)
        self.league_averages = defaultdict(lambda: {
            'shots': 10,
            'shots_on_target': 3.5,
            'xg': 1.2,
            'corners': 4.5,
            'possession': 50,
            'dangerous_attacks': 20,
            'passes': 400,
            'fouls': 12,
            'yellow_cards': 2
        })
        
        logger.info("Predictor (XGBoost) инициализирован")
    
    def _init_xgb_model(self):
        """Инициализирует XGBoost модель с оптимальными параметрами"""
        try:
            if os.path.exists(self.model_path):
                self.xgb_model = joblib.load(self.model_path)
                # Загружаем feature_names если есть
                if os.path.exists(self.model_path.replace('.pkl', '_features.json')):
                    with open(self.model_path.replace('.pkl', '_features.json'), 'r') as f:
                        self.feature_names = json.load(f)
                logger.info(f"✅ Загружена XGBoost модель из {self.model_path}")
            else:
                # Параметры из futbol_corners_forecast, адаптированные для голов
                self.xgb_model = xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.03,
                    reg_alpha=2.0,
                    reg_lambda=3.0,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    colsample_bylevel=0.7,
                    gamma=0.5,
                    min_child_weight=3,
                    scale_pos_weight=1.2,
                    random_state=42,
                    eval_metric='logloss',
                    use_label_encoder=False
                )
                logger.info("✅ Создана новая XGBoost модель")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации XGBoost: {e}")
            # Fallback на простую версию
            self.xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=3,
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
        """Предсказание с использованием XGBoost и продвинутых признаков"""
        try:
            # Получаем все необходимые данные
            home_stats = self._extract_team_stats(match, is_home=True)
            away_stats = self._extract_team_stats(match, is_home=False)
            
            # Если статистика отсутствует, используем базовые значения
            if not home_stats.get('has_real_stats', True):
                logger.debug(f"Матч {match.id}: используем базовую статистику")
            
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
            
            # Устанавливаем средние по лиге
            if match.league_id:
                self.feature_engineer.set_league_averages(
                    match.league_id, 
                    self.league_averages[match.league_id]
                )
            
            # Создаем признаки (60+ признаков)
            features = self.feature_engineer.create_all_features(
                match, home_stats, away_stats, home_form, away_form, h2h_data, match.league_id
            )
            
            # Сохраняем имена признаков
            if not self.feature_names and self.feature_engineer.feature_names:
                self.feature_names = self.feature_engineer.feature_names
            
            # ПРОВЕРКА: обучена ли XGBoost модель?
            xgb_available = False
            try:
                # Пробуем получить booster - если не обучен, будет ошибка
                if self.xgb_model and hasattr(self.xgb_model, 'get_booster'):
                    _ = self.xgb_model.get_booster()
                    xgb_available = True
            except:
                xgb_available = False
            
            if xgb_available:
                # Масштабируем признаки
                features_scaled = self.scaler.transform(features) if len(features.shape) > 1 else features
                
                # Получаем вероятность гола от XGBoost
                xgb_proba = self.xgb_model.predict_proba(features_scaled)[0][1]
                goal_probability = xgb_proba
                logger.debug(f"Матч {match.id}: XGBoost вероятность {goal_probability:.3f}")
            else:
                # Fallback на старую систему
                logger.debug(f"Матч {match.id}: XGBoost не обучен, используем legacy систему")
                goal_probability = self._calculate_legacy_probability(
                    home_stats, away_stats, home_form, away_form, h2h_data, match
                )
            
            # Калибруем вероятность
            goal_probability = self._calibrate_probability(goal_probability)
            
            # Добавляем небольшую вариацию для разнообразия
            variation = random.uniform(0.95, 1.05)
            goal_probability = min(0.95, max(0.1, goal_probability * variation))
            
            # Определяем уровень уверенности
            confidence_level = self._determine_confidence_level(goal_probability)
            
            # Генерируем сигнал
            match_url = self._generate_match_url(match)
            signal = self._generate_signal(
                match, goal_probability, confidence_level, 
                home_stats, away_stats, home_form, away_form, match_url
            )
            
            result = {
                'match_id': match.id,
                'match': match,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'league_name': match.league_name,
                'country_code': match.home_team.country_code if match.home_team else None,
                'goal_probability': round(goal_probability, 3),
                'confidence_level': confidence_level,
                'signal': signal,
                'home_stats': home_stats,
                'away_stats': away_stats,
                'home_form': home_form,
                'away_form': away_form,
                'h2h_data': h2h_data,
                'match_url': match_url,
                'league_id': match.league_id,
                'minute': match.minute,
                'features': features.flatten().tolist() if hasattr(features, 'flatten') else None,
                'timestamp': datetime.now().isoformat()
            }
            
            self._add_to_history(result)
            
            # Периодически пробуем обучать XGBoost
            if len(self.predictions_history) % 50 == 0 and not xgb_available:
                self._train_xgboost_on_history()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при предсказании матча {match.id}: {e}")
            logger.error(traceback.format_exc())
            return self._get_default_prediction(match)
            
            if len(self.predictions_history) % 10 == 0:  # Сохраняем каждые 10 предсказаний
                self.save_predictions()
    
    def _train_xgboost_on_history(self):
        """Обучает XGBoost модель на исторических данных"""
        try:
            if len(self.predictions_history) < 100:
                logger.info(f"⚠️ Недостаточно данных для обучения XGBoost: {len(self.predictions_history)} < 100")
                return False
            
            logger.info("🔄 Начинаем обучение XGBoost на исторических данных...")
            
            # Собираем данные для обучения
            X_train = []
            y_train = []
            
            for pred in self.predictions_history[-500:]:  # Используем последние 500 матчей
                if 'error' in pred and pred['error']:
                    continue
                
                match = pred.get('match')
                if not match or not hasattr(match, 'total_goals'):
                    continue
                
                # Получаем признаки (нужно сохранять их в истории)
                features = pred.get('features')
                if features is not None:
                    X_train.append(features)
                    y_train.append(1 if match.total_goals > 0 else 0)
            
            if len(X_train) < 50:
                logger.info(f"⚠️ Недостаточно валидных данных для обучения: {len(X_train)} < 50")
                return False
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Масштабируем
            X_scaled = self.scaler.fit_transform(X_train)
            
            # Обучаем XGBoost
            self.xgb_model.fit(
                X_scaled, y_train,
                eval_set=[(X_scaled, y_train)],
                verbose=False
            )
            
            # Получаем важность признаков
            if hasattr(self.xgb_model, 'feature_importances_'):
                importance_dict = {}
                for name, imp in zip(self.feature_names, self.xgb_model.feature_importances_):
                    importance_dict[name] = float(imp)
                self.accuracy_stats['feature_importance'] = importance_dict
                
                # Выводим топ-10 признаков
                top_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:10]
                logger.info("📊 Топ-10 важных признаков:")
                for name, imp in top_features:
                    logger.info(f"   {name}: {imp:.4f}")
            
            # Сохраняем модель
            self.save_predictions()
            logger.info(f"✅ XGBoost модель успешно обучена на {len(X_train)} примерах")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения XGBoost: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _calculate_legacy_probability(self, home_stats, away_stats, home_form, away_form, h2h_data, match) -> float:
        """Старая система расчета вероятности (fallback)"""
        # Получаем факторы
        h2h_factor = 1.0
        if h2h_data and h2h_data.get('matches_played', 0) > 0:
            h2h_factor = 1.0 + (h2h_data['team1_wins'] - h2h_data['team2_wins']) / h2h_data['matches_played'] * 0.1
        
        league_factor = self._get_league_factor(match)
        
        # Рассчитываем вероятности
        home_prob = self._calculate_goal_probability_legacy(
            home_stats, is_home=True, team_form=home_form,
            h2h_factor=h2h_factor, league_factor=league_factor
        )
        
        away_prob = self._calculate_goal_probability_legacy(
            away_stats, is_home=False, team_form=away_form,
            h2h_factor=1/h2h_factor, league_factor=league_factor
        )
        
        # Общая вероятность гола
        total_prob = 1 - (1 - home_prob) * (1 - away_prob)
        return total_prob
    
    def _calculate_goal_probability_legacy(self, stats: Dict, is_home: bool = True, 
                                          team_form: Optional[Dict] = None,
                                          h2h_factor: float = 1.0,
                                          league_factor: float = 1.0) -> float:
        """Старая функция расчета вероятности гола"""
        factors = []
        total_weight = 0
        
        has_real_stats = any([
            stats.get('shots', 0) > 0,
            stats.get('shots_on_target', 0) > 0
        ])
        
        if not has_real_stats:
            base_prob = 0.25 + (0.05 if is_home else 0)
            if team_form:
                form_factor = team_form.get('weighted_form', team_form.get('form', 0.5))
                base_prob += (form_factor - 0.5) * 0.15
            base_prob *= h2h_factor
            base_prob *= league_factor
            return max(0.1, min(0.6, base_prob))
        
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
        
        if team_form and 'team_form' in self.weights:
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
        return max(0.1, min(0.8, probability))
    
    def _get_league_factor(self, match: Match) -> float:
        """Фактор силы лиги"""
        if not match.league_id:
            return 1.0
        level = self.league_levels.get(match.league_id, 2)
        return 1.1 if level == 1 else 0.95
    
    def _calibrate_probability(self, probability: float) -> float:
        """Калибровка вероятности на основе исторических данных"""
        if len(self.accuracy_stats['calibration_data']) < 100:
            return probability
        
        calibration_data = self.accuracy_stats['calibration_data'][-100:]
        bins = np.linspace(0, 1, 11)
        
        for i in range(len(bins) - 1):
            bin_low, bin_high = bins[i], bins[i + 1]
            bin_probs = [p for p, actual in calibration_data if bin_low <= p < bin_high]
            bin_actuals = [actual for p, actual in calibration_data if bin_low <= p < bin_high]
            
            if bin_probs and abs(probability - np.mean(bin_probs)) < 0.05:
                return np.mean(bin_actuals)
        
        return probability
    
    def _determine_confidence_level(self, probability: float) -> str:
        """Определяет уровень уверенности"""
        if probability >= self.thresholds['very_high']:
            base = "VERY_HIGH"
        elif probability >= self.thresholds['high']:
            base = "HIGH"
        elif probability >= self.thresholds['medium']:
            base = "MEDIUM"
        elif probability >= self.thresholds['low']:
            base = "LOW"
        else:
            base = "VERY_LOW"
        
        # Корректировка на основе исторической точности
        if len(self.accuracy_stats['calibration_data']) > 50:
            level_stats = self.accuracy_stats['by_confidence'].get(base, {'total': 0, 'correct': 0})
            if level_stats['total'] > 5:
                hist_acc = level_stats['correct'] / level_stats['total']
                if hist_acc > 0.65 and base in ["MEDIUM", "LOW"]:
                    return "HIGH" if base == "MEDIUM" else "MEDIUM"
                elif hist_acc < 0.35 and base in ["VERY_HIGH", "HIGH"]:
                    return "HIGH" if base == "VERY_HIGH" else "MEDIUM"
        
        return base
    
    def _should_send_signal(self, prediction: Dict) -> bool:
        """
        Определяет, нужно ли отправлять сигнал.
        Отправляем только если вероятность >= min_signal_probability (46% по умолчанию)
        """
        if prediction.get('error', False):
            return False
        
        prob = prediction.get('goal_probability', 0)
        conf = prediction.get('confidence_level', 'LOW')
        
        # Основное условие: вероятность >= минимального порога
        if prob >= self.min_signal_probability:
            # Для VERY_HIGH и HIGH отправляем всегда
            if conf in ['VERY_HIGH', 'HIGH']:
                logger.debug(f"✅ Сигнал: {prob*100:.1f}% ({conf}) - ОТПРАВЛЯЕМ")
                return True
            # Для MEDIUM отправляем только если вероятность на 2% выше порога
            if conf == 'MEDIUM' and prob >= self.min_signal_probability + 0.02:
                logger.debug(f"✅ Сигнал: {prob*100:.1f}% (MEDIUM) - ОТПРАВЛЯЕМ")
                return True
            # Для LOW отправляем только при очень высокой вероятности (+9%)
            if conf == 'LOW' and prob >= self.min_signal_probability + 0.09:
                logger.debug(f"✅ Сигнал: {prob*100:.1f}% (LOW) - ОТПРАВЛЯЕМ")
                return True
            else:
                logger.debug(f"⏳ Сигнал: {prob*100:.1f}% ({conf}) - ПРОПУСК (недостаточно уверенности)")
                self.accuracy_stats['signals_filtered_out'] += 1
        else:
            logger.debug(f"⏳ Сигнал: {prob*100:.1f}% - ПРОПУСК (ниже {self.min_signal_probability*100:.0f}%)")
            self.accuracy_stats['signals_filtered_out'] += 1
        
        return False
    
    def _generate_signal(self, match: Match, goal_prob: float, confidence: str,
                        home_stats: Dict, away_stats: Dict,
                        home_form: Optional[Dict], away_form: Optional[Dict],
                        match_url: str) -> Dict:
        """Генерирует сигнал с расширенной статистикой"""
        confidence_emojis = {
            "VERY_HIGH": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
            "LOW": "🟢", "VERY_LOW": "⚪"
        }
        emoji = confidence_emojis.get(confidence, "⚪")
        
        home_name = match.home_team.name if match.home_team else "Home"
        away_name = match.away_team.name if match.away_team else "Away"
        
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
        
        # Проверяем наличие статистики
        has_stats = any([
            home_stats.get('shots', 0) > 0,
            away_stats.get('shots', 0) > 0,
            home_stats.get('shots_on_target', 0) > 0,
            away_stats.get('shots_on_target', 0) > 0
        ])
        
        message_lines = [
            f"{emoji} **⚽ ПОТЕНЦИАЛЬНЫЙ ГОЛ!**",
            f"⚔️ **{home_name} vs {away_name}**{league_info}",
            f"📊 **Счет:** {current_score}",
            f"⏱️ **Минута:** {match.minute or 0}' {period}",
            "",
            f"📈 **Вероятность гола:** {goal_prob*100:.1f}%",
            f"🎯 **Уверенность:** {confidence}",
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
            ])
        
        # Добавляем форму команд
        if home_form or away_form:
            message_lines.extend(["", "📈 **ФОРМА КОМАНД:**"])
            if home_form:
                form_str = home_form.get('form_string', '')
                ppg = home_form.get('points_per_game', 0)
                message_lines.append(f"  • {home_name}: {form_str} ({ppg:.1f} о/м)")
            if away_form:
                form_str = away_form.get('form_string', '')
                ppg = away_form.get('points_per_game', 0)
                message_lines.append(f"  • {away_name}: {form_str} ({ppg:.1f} о/м)")
        
        # Добавляем информацию о голах в таймах
        if match.id in self.half_goals:
            first = self.half_goals[match.id].get('first', 0)
            second = self.half_goals[match.id].get('second', 0)
            if first > 0 or second > 0:
                message_lines.extend([
                    "",
                    f"⚽️ **ГОЛЫ ПО ТАЙМАМ:**",
                    f"  • 1-й тайм: {first}",
                    f"  • 2-й тайм: {second}"
                ])
        
        message_lines.extend(["", f"🔗 **Смотреть матч:** {match_url}"])
        
        signal = {
            'emoji': emoji,
            'message': "\n".join(message_lines),
            'confidence': confidence,
            'probability': goal_prob,
            'match_id': match.id,
            'current_score': current_score,
            'match_url': match_url,
            'stats': {'home': home_stats, 'away': away_stats},
            'form': {'home': home_form, 'away': away_form},
            'league_name': match.league_name,
            'country_code': match.home_team.country_code if match.home_team else None,
            'timestamp': datetime.now()
        }
        
        return signal
    
    def analyze_live_match(self, match: Match) -> Optional[Dict]:
        """Анализирует live-матч и генерирует сигнал"""
        try:
            # Проверки на дублирование
            if match.id in self.match_signal_count:
                if self.match_signal_count[match.id] >= self.max_signals_per_match:
                    return None
            if match.id in self.match_last_signal:
                time_since = (datetime.now() - self.match_last_signal[match.id]).total_seconds()
                if time_since < self.min_time_between_signals:
                    return None
            
            if not self._should_analyze_match(match):
                return None
            
            prediction = self.predict_match(match)
            
            # Проверяем, нужно ли отправлять сигнал (с фильтром 46%)
            if self._should_send_signal(prediction):
                half = "1-й тайм" if match.minute and match.minute < 45 else "2-й тайм"
                
                self.match_last_signal[match.id] = datetime.now()
                self.match_signal_count[match.id] = self.match_signal_count.get(match.id, 0) + 1
                self.accuracy_stats['signals_sent_46plus'] += 1
                
                logger.info(f"📢 СИГНАЛ ОТПРАВЛЕН! Матч {match.id} ({half}) - {prediction['goal_probability']*100:.1f}%")
                
                if match.is_finished and hasattr(self, 'team_analyzer'):
                    self._save_match_to_history(match)
                    self.update_accuracy(str(match.id), match.total_goals)
                
                return prediction.get('signal')
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе матча {match.id}: {e}")
            return None
    
    def _should_analyze_match(self, match: Match) -> bool:
        """Проверяет, стоит ли анализировать матч"""
        if match.minute and match.minute > 75:
            return False
        if abs((match.home_score or 0) - (match.away_score or 0)) >= 3:
            return False
        if (match.home_score or 0) >= 4 or (match.away_score or 0) >= 4:
            return False
        return True
    
    def _generate_match_url(self, match: Match) -> str:
        """Генерирует ссылку на матч"""
        if not match.home_team or not match.away_team:
            return "https://www.sofascore.com"
        
        def slugify(name: str) -> str:
            # Простая транслитерация
            translit = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n'}
            name = name.lower().replace(' ', '-')
            for k, v in translit.items():
                name = name.replace(k, v)
            return ''.join(c for c in name if c.isalnum() or c == '-')
        
        home_slug = slugify(match.home_team.name)
        away_slug = slugify(match.away_team.name)
        return f"https://www.sofascore.com/ru/football/match/{home_slug}-vs-{away_slug}/{match.id}"
    
    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        """Извлекает статистику команды"""
        stats = {
            'shots': 0, 'shots_on_target': 0, 'corners': 0,
            'possession': 50, 'dangerous_attacks': 0, 'xg': 0.5,
            'passes': 0, 'fouls': 0, 'yellow_cards': 0,
            'goals': match.home_score if is_home else match.away_score,
            'has_real_stats': True
        }
        
        if not match.stats or not isinstance(match.stats, dict):
            stats['has_real_stats'] = False
            return stats
        
        # Прямое извлечение из словаря
        prefix = 'home' if is_home else 'away'
        stats['shots'] = match.stats.get(f'shots_{prefix}', 0)
        stats['shots_on_target'] = match.stats.get(f'shots_ontarget_{prefix}', 0)
        stats['possession'] = match.stats.get(f'possession_{prefix}', 50)
        stats['corners'] = match.stats.get(f'corners_{prefix}', 0)
        stats['dangerous_attacks'] = match.stats.get(f'dangerous_attacks_{prefix}', 0)
        stats['xg'] = match.stats.get(f'xg_{prefix}', 0.5)
        stats['passes'] = match.stats.get(f'passes_{prefix}', 0)
        stats['fouls'] = match.stats.get(f'fouls_{prefix}', 0)
        stats['yellow_cards'] = match.stats.get(f'yellow_cards_{prefix}', 0)
        stats['has_real_stats'] = match.stats.get('has_real_stats', True)
        
        return stats
    
    def _save_match_to_history(self, match):
        """Сохраняет завершенный матч в историю"""
        try:
            if not match or not match.is_finished:
                return
            if not match.home_team or not match.away_team:
                return
            
            self.team_analyzer.save_match(
                match_id=match.id,
                home_id=match.home_team.id,
                away_id=match.away_team.id,
                home_score=match.home_score or 0,
                away_score=match.away_score or 0,
                match_date=match.start_time or datetime.now(),
                league_id=match.league_id
            )
            
            # Обновляем средние по лиге
            if match.league_id and match.stats and isinstance(match.stats, dict):
                league_avg = self.league_averages[match.league_id]
                for key in ['shots', 'shots_on_target', 'xg', 'corners', 'possession', 'passes', 'fouls', 'yellow_cards']:
                    home_val = match.stats.get(f'{key}_home', 0)
                    away_val = match.stats.get(f'{key}_away', 0)
                    if home_val > 0 or away_val > 0:
                        league_avg[key] = (league_avg[key] * 0.95 + (home_val + away_val) / 2 * 0.05)
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения матча {match.id}: {e}")
    
    def update_accuracy(self, prediction_id: str, actual_goals: int):
        """Обновляет статистику точности"""
        try:
            for pred in self.predictions_history:
                if str(pred.get('match_id')) == str(prediction_id):
                    prob = pred.get('goal_probability', 0)
                    conf = pred.get('confidence_level', 'MEDIUM')
                    minute = pred.get('minute', 0)
                    league_id = pred.get('league_id')
                    
                    had_goal = actual_goals > 0
                    predicted_goal = prob > 0.5
                    
                    self.accuracy_stats['total_predictions'] += 1
                    self.accuracy_stats['calibration_data'].append((prob, 1 if had_goal else 0))
                    
                    if len(self.accuracy_stats['calibration_data']) > 1000:
                        self.accuracy_stats['calibration_data'] = self.accuracy_stats['calibration_data'][-1000:]
                    
                    if conf in self.accuracy_stats['by_confidence']:
                        self.accuracy_stats['by_confidence'][conf]['total'] += 1
                        if had_goal == predicted_goal:
                            self.accuracy_stats['by_confidence'][conf]['correct'] += 1
                    
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
                    
                    total = self.accuracy_stats['correct_predictions'] + self.accuracy_stats['incorrect_predictions']
                    if total > 0:
                        self.accuracy_stats['accuracy_rate'] = self.accuracy_stats['correct_predictions'] / total
                    
                    break
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
    
    def _add_to_history(self, prediction: Dict):
        """Добавляет предсказание в историю"""
        self.predictions_history.append(prediction)
        
        if len(self.predictions_history) > self.max_history_size:
            self.predictions_history = self.predictions_history[-self.max_history_size:]
    
    def _get_default_prediction(self, match: Match) -> Dict:
        """Предсказание по умолчанию"""
        return {
            'match_id': match.id,
            'match': match,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'goal_probability': 0.3,
            'confidence_level': 'LOW',
            'signal': None,
            'home_stats': {},
            'away_stats': {},
            'error': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_filtered_signals_stats(self) -> Dict:
        """
        Возвращает статистику по отфильтрованным сигналам
        """
        total_signals = len([p for p in self.predictions_history if p.get('signal')])
        signals_above_46 = len([p for p in self.predictions_history 
                               if p.get('signal') and p.get('goal_probability', 0) >= self.min_signal_probability])
        signals_below_46 = total_signals - signals_above_46
        
        return {
            'total_signals_generated': total_signals,
            'signals_sent_46plus': self.accuracy_stats.get('signals_sent_46plus', 0),
            'signals_filtered_out': self.accuracy_stats.get('signals_filtered_out', 0),
            'filter_rate': self.accuracy_stats.get('signals_filtered_out', 0) / total_signals if total_signals > 0 else 0,
            'min_probability': self.min_signal_probability
        }
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику"""
        if not self.predictions_history:
            return {
                'total_predictions': 0,
                'avg_probability': 0,
                'signals_sent': self.accuracy_stats['total_signals'],
                'signals_sent_46plus': self.accuracy_stats.get('signals_sent_46plus', 0),
                'signals_filtered_out': self.accuracy_stats.get('signals_filtered_out', 0),
                'accuracy_rate': self.accuracy_stats['accuracy_rate'],
                'feature_importance': self.accuracy_stats['feature_importance'],
                'by_confidence': self.accuracy_stats['by_confidence']
            }
        
        total = len(self.predictions_history)
        probs = [p.get('goal_probability', 0) for p in self.predictions_history]
        
        conf_dist = defaultdict(int)
        for p in self.predictions_history:
            conf_dist[p.get('confidence_level', 'UNKNOWN')] += 1
        for k in conf_dist:
            conf_dist[k] /= total
        
        return {
            'total_predictions': total,
            'avg_probability': np.mean(probs),
            'signals_sent': self.accuracy_stats['total_signals'],
            'signals_sent_46plus': self.accuracy_stats.get('signals_sent_46plus', 0),
            'signals_filtered_out': self.accuracy_stats.get('signals_filtered_out', 0),
            'accuracy_rate': self.accuracy_stats['accuracy_rate'],
            'confidence_distribution': dict(conf_dist),
            'feature_importance': self.accuracy_stats['feature_importance'],
            'by_confidence': self.accuracy_stats['by_confidence']
        }
    
    def save_predictions(self, filename: str = 'data/predictions.json'):
        """Сохраняет предсказания"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            data = {
                'predictions': [],
                'accuracy_stats': self.accuracy_stats,
                'thresholds': self.thresholds,
                'half_goals': self.half_goals,
                'match_signal_count': self.match_signal_count,
                'min_signal_probability': self.min_signal_probability
            }
            
            for p in self.predictions_history:
                p_copy = p.copy()
                if 'match' in p_copy:
                    del p_copy['match']
                data['predictions'].append(p_copy)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Сохраняем XGBoost модель
            if self.xgb_model and hasattr(self.xgb_model, 'get_booster'):
                try:
                    _ = self.xgb_model.get_booster()  # Проверяем, что модель обучена
                    joblib.dump(self.xgb_model, self.model_path)
                    if self.feature_names:
                        with open(self.model_path.replace('.pkl', '_features.json'), 'w') as f:
                            json.dump(self.feature_names, f)
                except:
                    pass
            
            logger.info(f"💾 Сохранено {len(data['predictions'])} предсказаний")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    
    def load_predictions(self, filename: str = 'data/predictions.json'):
        """Загружает предсказания"""
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
                logger.info(f"📂 Загружено {len(self.predictions_history)} предсказаний")
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")