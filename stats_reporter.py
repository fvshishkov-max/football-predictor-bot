# stats_reporter.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from collections import defaultdict
import numpy as np

from models import Match
from betting_optimizer import BettingOptimizer

logger = logging.getLogger(__name__)

class StatsReporter:
    """Класс для сбора и отправки статистики прогнозов"""
    
    def __init__(self, telegram_bot, predictor):
        self.telegram_bot = telegram_bot
        self.predictor = predictor
        self.betting_opt = BettingOptimizer(initial_bankroll=1000.0)
        self.stats_file = 'data/prediction_stats.json'
        self.pending_predictions = {}  # Словарь для отслеживания необработанных прогнозов
        self.load_stats()
        
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
                    'last_report': None
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
    
    def register_prediction(self, match_id: int, prediction: Dict):
        """Регистрирует прогноз для последующего отслеживания"""
        self.pending_predictions[match_id] = {
            'prediction': prediction,
            'timestamp': datetime.now(),
            'match_minute': prediction.get('minute', 0),
            'home_score': 0,
            'away_score': 0,
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
        
        # Обновляем статистику по уровням уверенности
        if confidence in self.stats['by_confidence']:
            self.stats['by_confidence'][confidence]['total'] += 1
            if was_correct:
                self.stats['by_confidence'][confidence]['correct'] += 1
        
        # Обновляем статистику по минутам
        minute_range = (minute // 15) * 15
        minute_key = f"{minute_range}-{minute_range+15}"
        
        if minute_key not in self.stats['by_minute']:
            self.stats['by_minute'][minute_key] = {'total': 0, 'correct': 0}
        
        self.stats['by_minute'][minute_key]['total'] += 1
        if was_correct:
            self.stats['by_minute'][minute_key]['correct'] += 1
        
        # Обновляем статистику по лигам
        if league_id:
            league_key = f"league_{league_id}"
            if league_key not in self.stats['by_league']:
                self.stats['by_league'][league_key] = {'total': 0, 'correct': 0}
            
            self.stats['by_league'][league_key]['total'] += 1
            if was_correct:
                self.stats['by_league'][league_key]['correct'] += 1
        
        # Пересчитываем общую точность
        total = self.stats['correct_predictions'] + self.stats['incorrect_predictions']
        if total > 0:
            self.stats['accuracy_rate'] = self.stats['correct_predictions'] / total
        
        # Добавляем в историю последних матчей
        self.stats['recent_matches'].append({
            'match_id': prediction.get('match_id'),
            'home_team': prediction.get('home_team'),
            'away_team': prediction.get('away_team'),
            'probability': prediction.get('total_goal_probability', 0),
            'confidence': confidence,
            'minute': minute,
            'league_id': league_id,
            'was_correct': was_correct,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем историю до 100 матчей
        if len(self.stats['recent_matches']) > 100:
            self.stats['recent_matches'] = self.stats['recent_matches'][-100:]
        
        # Обновляем финансовую статистику
        self._update_financial_stats(prediction, was_correct)
        
        self.save_stats()
        
        # Проверяем, нужно ли отправить отчет (каждые 10 матчей)
        if self.stats['total_predictions'] % 10 == 0:
            self.send_periodic_report()
    
    def _update_financial_stats(self, prediction: Dict, was_correct: bool):
        """Обновляет финансовую статистику"""
        try:
            odds = 1.95
            probability = prediction.get('total_goal_probability', 0.5)
            
            kelly_fraction = self.betting_opt.kelly_criterion(probability, odds)
            stake = self.betting_opt.current_bankroll * kelly_fraction
            
            bet = self.betting_opt.place_bet(probability, odds, stake)
            self.betting_opt.settle_bet(len(self.betting_opt.bet_history) - 1, was_correct)
            
            report = self.betting_opt.get_performance_report()
            self.stats['financial_stats'] = report
            
        except Exception as e:
            logger.error(f"Ошибка обновления финансовой статистики: {e}")
    
    def check_prediction_accuracy(self, match: Match, prediction: Dict):
        """Проверяет точность прогноза после завершения матча"""
        if not match.is_finished:
            # Если матч не завершен, просто регистрируем прогноз
            self.register_prediction(match.id, prediction)
            return
        
        had_goal = match.total_goals > 0
        predicted_prob = prediction.get('probability', 0) / 100
        predicted_goal = predicted_prob > 0.5
        
        was_correct = (had_goal == predicted_goal)
        
        prediction_data = {
            'match_id': match.id,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'total_goal_probability': predicted_prob,
            'confidence_level': prediction.get('confidence', 'MEDIUM'),
            'minute': match.minute,
            'league_id': match.league_id
        }
        
        self.update_stats(prediction_data, was_correct)
        
        # Отправляем уведомление о результате
        self.send_result_notification(match, prediction, was_correct)
        
        # Удаляем из списка ожидающих
        if match.id in self.pending_predictions:
            del self.pending_predictions[match.id]
    
    def check_goal_scored(self, match: Match, prediction: Dict):
        """Проверяет, был ли забит гол после прогноза"""
        if match.id not in self.pending_predictions:
            return
        
        pending = self.pending_predictions[match.id]
        if pending['processed']:
            return
        
        # Проверяем, изменился ли счет
        if match.home_score > pending['home_score'] or match.away_score > pending['away_score']:
            # Гол забит!
            logger.info(f"⚽ ГОЛ после прогноза в матче {match.id}!")
            
            # Отправляем уведомление о голе
            self.send_goal_notification(match, prediction)
            
            pending['processed'] = True
    
    def send_result_notification(self, match: Match, prediction: Dict, was_correct: bool):
        """Отправляет уведомление о результате прогноза через send_goal_signal"""
        try:
            from models import MatchAnalysis, GoalSignal, LiveStats
            
            # Создаем простой анализ для передачи в сигнал
            stats = LiveStats(minute=match.minute or 0)
            goal_signal = GoalSignal(
                match_id=match.id,
                predicted_minute=match.minute or 0,
                probability=prediction.get('probability', 0),
                signal_type=prediction.get('confidence', 'MEDIUM'),
                description=f"Результат прогноза",
                timestamp=datetime.now(),
                stats=stats.to_dict(),
                minutes_left=0
            )
            analysis = MatchAnalysis(
                match_id=match.id,
                timestamp=datetime.now(),
                minute=match.minute or 0,
                score=f"{match.home_score}:{match.away_score}",
                stats=stats,
                activity_level="NORMAL",
                activity_description="Матч завершен",
                attack_potential="NORMAL",
                next_signal=goal_signal,
                has_signal=True
            )
            
            if was_correct:
                emoji = "✅"
                title = "ПРОГНОЗ СЫГРАЛ!"
            else:
                emoji = "❌"
                title = "ПРОГНОЗ НЕ СЫГРАЛ"
            
            # Получаем статистику точности
            last_10 = self.stats['recent_matches'][-10:]
            last_10_correct = sum(1 for m in last_10 if m['was_correct'])
            last_10_accuracy = (last_10_correct / len(last_10)) * 100 if last_10 else 0
            
            message = (
                f"{emoji} **{title}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚔️ {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Итоговый счет: {match.home_score}:{match.away_score}\n\n"
                f"📈 Прогноз: {prediction.get('probability', 0):.1f}%\n"
                f"🎯 Уверенность: {prediction.get('confidence', 'MEDIUM')}\n"
                f"📊 Прогнозировался гол: {'ДА' if prediction.get('probability', 0) > 50 else 'НЕТ'}\n"
                f"⚽ Голы в матче: {'БЫЛИ' if match.total_goals > 0 else 'НЕТ'}\n\n"
                f"📊 Точность за последние 10 матчей: {last_10_accuracy:.1f}%\n"
            )
            
            if was_correct:
                message += f"\n🔥 Отличная работа! Прогноз подтвердился."
            else:
                message += f"\n💪 В следующий раз повезет больше!"
            
            # Используем send_goal_signal вместо send_message
            self.telegram_bot.send_goal_signal(match, analysis, message)
            logger.info(f"{emoji} Отправлено уведомление о результате для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о результате: {e}")
    
    def send_goal_notification(self, match: Match, prediction: Dict):
        """Отправляет уведомление о забитом голе после прогноза через send_goal_signal"""
        try:
            from models import MatchAnalysis, GoalSignal, LiveStats
            
            # Создаем простой анализ для передачи в сигнал
            stats = LiveStats(minute=match.minute or 0)
            goal_signal = GoalSignal(
                match_id=match.id,
                predicted_minute=match.minute or 0,
                probability=prediction.get('probability', 0),
                signal_type=prediction.get('confidence', 'MEDIUM'),
                description=f"Гол после прогноза",
                timestamp=datetime.now(),
                stats=stats.to_dict(),
                minutes_left=90 - (match.minute or 0)
            )
            analysis = MatchAnalysis(
                match_id=match.id,
                timestamp=datetime.now(),
                minute=match.minute or 0,
                score=f"{match.home_score}:{match.away_score}",
                stats=stats,
                activity_level="HIGH",
                activity_description="Гол забит!",
                attack_potential="HIGH",
                next_signal=goal_signal,
                has_signal=True
            )
            
            message = (
                f"⚽ **ГОЛ ПОСЛЕ ПРОГНОЗА!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚔️ {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Текущий счет: {match.home_score}:{match.away_score}\n"
                f"⏱ Минута: {match.minute}'\n\n"
                f"📈 Прогноз был: {prediction.get('probability', 0):.1f}%\n"
                f"🎯 Уверенность: {prediction.get('confidence', 'MEDIUM')}\n\n"
                f"🔥 Прогноз сработал!"
            )
            
            # Используем send_goal_signal вместо send_message
            self.telegram_bot.send_goal_signal(match, analysis, message)
            logger.info(f"⚽ Отправлено уведомление о голе для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о голе: {e}")
    
    def send_periodic_report(self):
        """Отправляет периодический отчет в Telegram через send_goal_signal"""
        try:
            from models import MatchAnalysis, GoalSignal, LiveStats
            from datetime import datetime
            
            total = self.stats['total_predictions']
            correct = self.stats['correct_predictions']
            accuracy = self.stats['accuracy_rate'] * 100
            
            last_10 = self.stats['recent_matches'][-10:]
            last_10_correct = sum(1 for m in last_10 if m['was_correct'])
            last_10_accuracy = (last_10_correct / len(last_10)) * 100 if last_10 else 0
            
            confidence_stats = []
            for level, data in self.stats['by_confidence'].items():
                if data['total'] > 0:
                    level_acc = (data['correct'] / data['total']) * 100
                    confidence_stats.append(
                        f"  {level}: {data['total']} прогнозов, точность {level_acc:.1f}%"
                    )
            
            minute_stats = []
            for minute_range, data in sorted(self.stats['by_minute'].items()):
                if data['total'] > 0:
                    minute_acc = (data['correct'] / data['total']) * 100
                    minute_stats.append(
                        f"  {minute_range} мин: {data['total']} прогнозов, точность {minute_acc:.1f}%"
                    )
            
            fin = self.stats.get('financial_stats', {})
            
            message_lines = [
                f"📊 **ОТЧЕТ ПО ПРОГНОЗАМ**",
                f"━━━━━━━━━━━━━━━━━━━━━\n",
                f"📈 **Общая статистика:**",
                f"  • Всего прогнозов: {total}",
                f"  • Правильных: {correct}",
                f"  • Неправильных: {self.stats['incorrect_predictions']}",
                f"  • Общая точность: {accuracy:.1f}%\n",
                f"📊 **Последние 10 матчей:**",
                f"  • Правильных: {last_10_correct}/10",
                f"  • Точность: {last_10_accuracy:.1f}%\n",
                f"💰 **Финансовые показатели:**",
                f"  • Банкролл: {fin.get('current_bankroll', 1000):.2f}",
                f"  • ROI: {fin.get('roi_percent', 0):.1f}%",
                f"  • Коэф. Шарпа: {fin.get('sharpe_ratio', 0):.2f}",
                f"  • Profit Factor: {fin.get('profit_factor', 0):.2f}\n",
                f"🎯 **По уровням уверенности:**"
            ]
            
            message_lines.extend(confidence_stats)
            
            if minute_stats:
                message_lines.extend([
                    "",
                    "⏱ **По минутам:**"
                ])
                message_lines.extend(minute_stats)
            
            message_lines.extend([
                "",
                f"📅 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            ])
            
            message = "\n".join(message_lines)
            
            # Создаем фиктивный match и analysis для send_goal_signal
            dummy_match = type('Match', (), {
                'id': 0,
                'home_team': type('Team', (), {'name': 'Статистика'}),
                'away_team': type('Team', (), {'name': 'Прогнозов'}),
                'home_score': 0,
                'away_score': 0,
                'minute': 0,
                'is_finished': False
            })()
            
            stats = LiveStats(minute=0)
            goal_signal = GoalSignal(
                match_id=0,
                predicted_minute=0,
                probability=0,
                signal_type='INFO',
                description='Периодический отчет',
                timestamp=datetime.now(),
                stats=stats.to_dict(),
                minutes_left=0
            )
            analysis = MatchAnalysis(
                match_id=0,
                timestamp=datetime.now(),
                minute=0,
                score='0:0',
                stats=stats,
                activity_level='INFO',
                activity_description='Отчет',
                attack_potential='INFO',
                next_signal=goal_signal,
                has_signal=True
            )
            
            self.telegram_bot.send_goal_signal(dummy_match, analysis, message)
            self.stats['last_report'] = datetime.now().isoformat()
            logger.info(f"📊 Отправлен периодический отчет (матч #{total})")
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")