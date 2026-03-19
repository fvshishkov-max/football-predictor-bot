# stats_reporter.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from collections import defaultdict
import numpy as np
import threading
import time

from models import Match  # ВАЖНО: добавляем этот импорт
from betting_optimizer import BettingOptimizer

logger = logging.getLogger(__name__)

class StatsReporter:
    """Класс для сбора и отправки статистики прогнозов"""
    
    def __init__(self, telegram_bot, predictor):
        self.telegram_bot = telegram_bot
        self.predictor = predictor
        self.betting_opt = BettingOptimizer(initial_bankroll=1000.0)
        self.stats_file = 'data/prediction_stats.json'
        self.pending_predictions = {}
        self.load_stats()
        
        # Запускаем поток для отправки часовой статистики
        self.running = True
        self.stats_thread = threading.Thread(target=self._hourly_stats_loop, daemon=True)
        self.stats_thread.start()
        logger.info("⏰ Запущен поток часовой статистики")
        
    def load_stats(self):
        """Загружает статистику из файла"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'incorrect_predictions': 0,
                    'accuracy_rate': 0.0,
                    'by_confidence': {
                        'VERY_HIGH': {'total': 0, 'correct': 0},
                        'HIGH': {'total': 0, 'correct': 0},
                        'MEDIUM': {'total': 0, 'correct': 0},
                        'LOW': {'total': 0, 'correct': 0},
                        'VERY_LOW': {'total': 0, 'correct': 0}
                    },
                    'by_minute': {},
                    'by_league': {},
                    'recent_matches': [],
                    'financial_stats': {},
                    'last_report': None,
                    'hourly_stats': []
                }
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
            self.stats = {}
    
    def save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")
    
    def _hourly_stats_loop(self):
        """Поток для отправки статистики каждый час"""
        while self.running:
            try:
                now = datetime.now()
                next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                wait_seconds = (next_hour - now).total_seconds()
                
                logger.info(f"⏰ Следующий отчет через {wait_seconds/60:.0f} минут")
                time.sleep(wait_seconds)
                
                self.send_hourly_report()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в потоке часовой статистики: {e}")
                time.sleep(60)
    
    def send_hourly_report(self):
            """Отправляет часовой отчет на русском"""
            try:
                last_hour = datetime.now() - timedelta(hours=1)
                last_hour_matches = []
                
                for match in self.stats['recent_matches']:
                    try:
                        match_time = datetime.fromisoformat(match['timestamp'].replace('Z', '+00:00'))
                        if match_time > last_hour:
                            last_hour_matches.append(match)
                    except:
                        continue
                
                if not last_hour_matches:
                    logger.info("⏰ За последний час не было завершенных матчей")
                    return
                
                total = len(last_hour_matches)
                correct = sum(1 for m in last_hour_matches if m.get('was_correct', False))
                accuracy = (correct / total * 100) if total > 0 else 0
                
                message = (
                    f"⏰ ЧАСОВОЙ ОТЧЕТ\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📊 Завершено матчей за час: {total}\n"
                    f"✅ Сыграло прогнозов: {correct}\n"
                    f"❌ Не сыграло: {total - correct}\n"
                    f"🎯 Точность за час: {accuracy:.1f}%\n\n"
                    f"📈 Общая статистика:\n"
                    f"  • Всего прогнозов: {self.stats['total_predictions']}\n"
                    f"  • Общая точность: {self.stats['accuracy_rate']*100:.1f}%"
                )
                
                if self.telegram_bot:
                    self.telegram_bot.send_message_to_channel(message)
                logger.info(f"⏰ Отправлен часовой отчет ({total} матчей)")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки отчета: {e}")
    
    def register_prediction(self, match_id: int, prediction: Dict, match: Optional[Match] = None):
        """Регистрирует прогноз для последующего отслеживания"""
        minute = 0
        home_score = 0
        away_score = 0
        
        if match:
            minute = match.minute or 0
            home_score = match.home_score or 0
            away_score = match.away_score or 0
            
        self.pending_predictions[match_id] = {
            'prediction': prediction,
            'timestamp': datetime.now(),
            'match_minute': minute,
            'home_score': home_score,
            'away_score': away_score,
            'processed': False
        }
        logger.info(f"📝 Зарегистрирован прогноз для матча {match_id}")
    
    def update_stats(self, prediction: Dict, was_correct: bool):
        """Обновляет статистику на основе результата"""
        confidence = prediction.get('confidence_level', 'MEDIUM')
        minute = prediction.get('minute', 0)
        league_id = prediction.get('league_id')
        
        self.stats['total_predictions'] += 1
        if was_correct:
            self.stats['correct_predictions'] += 1
        else:
            self.stats['incorrect_predictions'] += 1
        
        if confidence in self.stats['by_confidence']:
            self.stats['by_confidence'][confidence]['total'] += 1
            if was_correct:
                self.stats['by_confidence'][confidence]['correct'] += 1
        
        minute_range = (minute // 15) * 15
        minute_key = f"{minute_range}-{minute_range+15}"
        
        if minute_key not in self.stats['by_minute']:
            self.stats['by_minute'][minute_key] = {'total': 0, 'correct': 0}
        
        self.stats['by_minute'][minute_key]['total'] += 1
        if was_correct:
            self.stats['by_minute'][minute_key]['correct'] += 1
        
        if league_id:
            league_key = f"league_{league_id}"
            if league_key not in self.stats['by_league']:
                self.stats['by_league'][league_key] = {'total': 0, 'correct': 0}
            
            self.stats['by_league'][league_key]['total'] += 1
            if was_correct:
                self.stats['by_league'][league_key]['correct'] += 1
        
        total = self.stats['correct_predictions'] + self.stats['incorrect_predictions']
        if total > 0:
            self.stats['accuracy_rate'] = self.stats['correct_predictions'] / total
        
        self.stats['recent_matches'].append({
            'match_id': prediction.get('match_id'),
            'home_team': prediction.get('home_team'),
            'away_team': prediction.get('away_team'),
            'probability': prediction.get('goal_probability', 0),
            'confidence': confidence,
            'minute': minute,
            'league_id': league_id,
            'was_correct': was_correct,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.stats['recent_matches']) > 100:
            self.stats['recent_matches'] = self.stats['recent_matches'][-100:]
        
        self.save_stats()
    
    def check_prediction_accuracy(self, match: Match, prediction: Dict):
        """Проверяет точность прогноза после завершения матча"""
        if not match.is_finished:
            self.register_prediction(match.id, prediction, match)
            return
        
        had_goal = match.total_goals > 0
        predicted_prob = prediction.get('probability', 0) / 100
        predicted_goal = predicted_prob > 0.5
        
        was_correct = (had_goal == predicted_goal)
        
        prediction_data = {
            'match_id': match.id,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'goal_probability': predicted_prob,
            'confidence_level': prediction.get('confidence', 'MEDIUM'),
            'minute': match.minute,
            'league_id': match.league_id,
            'was_correct': was_correct
        }
        
        self.update_stats(prediction_data, was_correct)
        
        if was_correct:
            self.send_success_notification(match, prediction)
        else:
            self.send_failed_prediction_notification(match, prediction)
        
        if match.id in self.pending_predictions:
            del self.pending_predictions[match.id]
    
    def check_goal_scored(self, match: Match, prediction: Dict):
        """Проверяет, был ли забит гол после прогноза"""
        if match.id not in self.pending_predictions:
            return
        
        pending = self.pending_predictions[match.id]
        if pending['processed']:
            return
        
        current_home = match.home_score or 0
        current_away = match.away_score or 0
        
        if current_home > pending['home_score'] or current_away > pending['away_score']:
            logger.info(f"⚽ ГОЛ после прогноза в матче {match.id}!")
            self.send_goal_notification(match, prediction)
            pending['processed'] = True
            pending['home_score'] = current_home
            pending['away_score'] = current_away
    
    def send_success_notification(self, match: Match, prediction: Dict):
        """Отправляет уведомление о совпадении прогноза"""
        try:
            prob = prediction.get('probability', 0)
            confidence = prediction.get('confidence', 'MEDIUM')
            
            confidence_text = {
                "VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ",
                "HIGH": "ВЫСОКАЯ",
                "MEDIUM": "СРЕДНЯЯ",
                "LOW": "НИЗКАЯ",
                "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"
            }.get(confidence, confidence)
            
            message = (
                f"✅ ПРОГНОЗ СЫГРАЛ!\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏟 {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Итоговый счет: {match.home_score}:{match.away_score}\n\n"
                f"📈 Прогноз: {prob:.1f}%\n"
                f"🎯 Уверенность: {confidence_text}\n\n"
                f"🔥 Отличная работа!"
            )
            
            if self.telegram_bot:
                self.telegram_bot.send_message_to_channel(message)
            logger.info(f"✅ Отправлено уведомление для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

    def send_failed_prediction_notification(self, match: Match, prediction: Dict):
        """Отправляет уведомление о том, что прогноз не зашел"""
        try:
            prob = prediction.get('probability', 0)
            confidence = prediction.get('confidence', 'MEDIUM')
            
            confidence_text = {
                "VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ",
                "HIGH": "ВЫСОКАЯ",
                "MEDIUM": "СРЕДНЯЯ",
                "LOW": "НИЗКАЯ",
                "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"
            }.get(confidence, confidence)
            
            message = (
                f"❌ ПРОГНОЗ НЕ СЫГРАЛ\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏟 {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Итоговый счет: {match.home_score}:{match.away_score}\n\n"
                f"📈 Прогноз был: {prob:.1f}%\n"
                f"🎯 Уверенность: {confidence_text}\n\n"
                f"💪 В следующий раз повезет больше!"
            )
            
            if self.telegram_bot:
                self.telegram_bot.send_message_to_channel(message)
            logger.info(f"❌ Отправлено уведомление для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

    def send_goal_notification(self, match: Match, prediction: Dict):
        """Отправляет уведомление о забитом голе"""
        try:
            prob = prediction.get('probability', 0)
            confidence = prediction.get('confidence', 'MEDIUM')
            
            confidence_text = {
                "VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ",
                "HIGH": "ВЫСОКАЯ",
                "MEDIUM": "СРЕДНЯЯ",
                "LOW": "НИЗКАЯ",
                "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"
            }.get(confidence, confidence)
            
            message = (
                f"⚽ ГОЛ ПОСЛЕ ПРОГНОЗА!\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏟 {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Текущий счет: {match.home_score}:{match.away_score}\n"
                f"⏱ Минута: {match.minute}'\n\n"
                f"📈 Прогноз был: {prob:.1f}%\n"
                f"🎯 Уверенность: {confidence_text}\n\n"
                f"🔥 Прогноз сработал!"
            )
            
            if self.telegram_bot:
                self.telegram_bot.send_message_to_channel(message)
            logger.info(f"⚽ Отправлено уведомление о голе для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def stop(self):
        """Останавливает поток статистики"""
        self.running = False
        if self.stats_thread.is_alive():
            self.stats_thread.join(timeout=5)
        logger.info("⏹ Поток часовой статистики остановлен")