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
            # Симулируем ставку с коэффициентом 1.95 (средний)
            odds = 1.95
            probability = prediction.get('total_goal_probability', 0.5)
            
            # Рассчитываем оптимальную ставку по Келли
            kelly_fraction = self.betting_opt.kelly_criterion(probability, odds)
            stake = self.betting_opt.current_bankroll * kelly_fraction
            
            # Размещаем ставку
            bet = self.betting_opt.place_bet(probability, odds, stake)
            
            # Рассчитываем результат
            self.betting_opt.settle_bet(len(self.betting_opt.bet_history) - 1, was_correct)
            
            # Получаем отчет
            report = self.betting_opt.get_performance_report()
            self.stats['financial_stats'] = report
            
        except Exception as e:
            logger.error(f"Ошибка обновления финансовой статистики: {e}")
    
    def send_periodic_report(self):
        """Отправляет периодический отчет в Telegram"""
        try:
            total = self.stats['total_predictions']
            correct = self.stats['correct_predictions']
            accuracy = self.stats['accuracy_rate'] * 100
            
            # Статистика за последние 10 матчей
            last_10 = self.stats['recent_matches'][-10:]
            last_10_correct = sum(1 for m in last_10 if m['was_correct'])
            last_10_accuracy = (last_10_correct / len(last_10)) * 100 if last_10 else 0
            
            # Статистика по уровням уверенности
            confidence_stats = []
            for level, data in self.stats['by_confidence'].items():
                if data['total'] > 0:
                    level_acc = (data['correct'] / data['total']) * 100
                    confidence_stats.append(
                        f"  {level}: {data['total']} прогнозов, точность {level_acc:.1f}%"
                    )
            
            # Статистика по минутам
            minute_stats = []
            for minute_range, data in sorted(self.stats['by_minute'].items()):
                if data['total'] > 0:
                    minute_acc = (data['correct'] / data['total']) * 100
                    minute_stats.append(
                        f"  {minute_range} мин: {data['total']} прогнозов, точность {minute_acc:.1f}%"
                    )
            
            # Финансовая статистика
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
                f"  • Profit Factor: {fin.get('profit_factor', 0):.2f}",
                f"  • Макс. просадка: {fin.get('max_drawdown', {}).get('max_drawdown', 0)*100:.1f}%\n",
                f"🎯 **По уровням уверенности:**"
            ]
            
            message_lines.extend(confidence_stats)
            
            if minute_stats:
                message_lines.extend([
                    "",
                    "⏱ **По минутам:**"
                ])
                message_lines.extend(minute_stats)
            
            # Добавляем регрессионную статистику из predictor
            predictor_stats = self.predictor.get_statistics()
            reg_stats = predictor_stats.get('regression_stats', {})
            
            if reg_stats:
                message_lines.extend([
                    "",
                    "📐 **Регрессионный анализ:**",
                    f"  • AIC: {reg_stats.get('aic', 0):.1f}",
                    f"  • R²: {reg_stats.get('pseudo_r_squared', 0):.3f}",
                    f"  • Log-Likelihood: {reg_stats.get('log_likelihood', 0):.1f}"
                ])
            
            message_lines.extend([
                "",
                f"📅 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            ])
            
            message = "\n".join(message_lines)
            
            self.telegram_bot.send_message(message)
            self.stats['last_report'] = datetime.now().isoformat()
            logger.info(f"📊 Отправлен периодический отчет (матч #{total})")
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    def check_prediction_accuracy(self, match: Match, prediction: Dict):
        """Проверяет точность прогноза после завершения матча"""
        if not match.is_finished:
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
        
        # Если прогноз совпал, отправляем уведомление
        if was_correct and prediction.get('signal'):
            self.send_success_notification(match, prediction)
    
    def send_success_notification(self, match: Match, prediction: Dict):
        """Отправляет уведомление о совпадении прогноза"""
        try:
            # Получаем статистику точности за последние 10 матчей
            last_10 = self.stats['recent_matches'][-10:]
            last_10_correct = sum(1 for m in last_10 if m['was_correct'])
            last_10_accuracy = (last_10_correct / len(last_10)) * 100 if last_10 else 0
            
            # Финансовая статистика
            fin = self.stats.get('financial_stats', {})
            
            message = (
                f"✅ **ПРОГНОЗ СЫГРАЛ!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚔️ {match.home_team.name} vs {match.away_team.name}\n"
                f"📊 Итоговый счет: {match.home_score}:{match.away_score}\n\n"
                f"📈 Прогноз: {prediction.get('probability', 0):.1f}%\n"
                f"🎯 Уверенность: {prediction.get('confidence', 'MEDIUM')}\n\n"
                f"📊 Точность за последние 10 матчей: {last_10_accuracy:.1f}%\n"
                f"💰 Текущий банкролл: {fin.get('current_bankroll', 1000):.2f}\n"
                f"📈 Коэф. Шарпа: {fin.get('sharpe_ratio', 0):.2f}\n\n"
                f"🔥 Отличная работа! Прогноз подтвердился."
            )
            
            self.telegram_bot.send_message(message)
            logger.info(f"✅ Отправлено уведомление о совпадении для матча {match.id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")