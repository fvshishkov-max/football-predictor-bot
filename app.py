import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List
import os
import asyncio

# Импортируем config целиком
import config
from api_client import SStatsClient
from predictor import Predictor
from telegram_bot import TelegramBot
from team_form import TeamFormAnalyzer
from stats_reporter import StatsReporter
from models import MatchAnalysis, GoalSignal, LiveStats, XGData

logger = logging.getLogger(__name__)

class FootballApp:
    """Основной класс приложения"""
    
    def __init__(self):
        """Инициализация приложения"""
        logger.info("=" * 50)
        logger.info("🚀 Инициализация FootballApp...")
        logger.info("=" * 50)
        
        try:
            # Получаем токены из config
            self.bot_token = getattr(config, 'TELEGRAM_TOKEN', None)
            self.channel_id = getattr(config, 'CHANNEL_ID', '-1001679913676')
            self.sstats_api_key = getattr(config, 'SSTATS_TOKEN', None)
            self.use_mock = getattr(config, 'USE_MOCK_API', False)
            self.check_interval = getattr(config, 'CHECK_INTERVAL', 600)
            
            # Логируем результаты
            logger.info(f"📱 TELEGRAM_TOKEN: {'Найден' if self.bot_token else 'НЕ НАЙДЕН'}")
            if self.bot_token:
                logger.info(f"    - первые 10 символов: {self.bot_token[:10]}...")
            
            logger.info(f"📢 CHANNEL_ID: {self.channel_id} (целевой канал)")
            logger.info(f"🔑 SSTATS_TOKEN: {'Найден' if self.sstats_api_key else 'НЕ НАЙДЕН'}")
            if self.sstats_api_key:
                logger.info(f"    - первые 5 символов: {self.sstats_api_key[:5]}...")
            
            logger.info(f"🎭 USE_MOCK_API: {self.use_mock}")
            
            # Проверяем наличие необходимых токенов
            if not self.bot_token:
                logger.error("❌ TELEGRAM_TOKEN не найден в config.py!")
                raise ValueError("TELEGRAM_TOKEN not found in config")
            
            if not self.sstats_api_key and not self.use_mock:
                logger.warning("⚠️ SSTATS_TOKEN не найден, переключаю в mock режим")
                self.use_mock = True
            
            # Инициализация компонентов
            logger.info("📡 Подключение к API...")
            self.api_client = SStatsClient(
                api_key=self.sstats_api_key if self.sstats_api_key else "mock_key",
                use_mock=self.use_mock
            )
            logger.info(f"✅ API клиент инициализирован (mock режим: {self.use_mock})")
            
            logger.info("🧠 Инициализация предиктора...")
            self.predictor = Predictor()
            logger.info("✅ Предиктор инициализирован")
            
            logger.info("📊 Инициализация анализатора формы команд...")
            self.team_analyzer = TeamFormAnalyzer()
            logger.info("✅ Анализатор формы инициализирован")
            
            logger.info("🤖 Инициализация Telegram бота...")
            self.telegram_bot = TelegramBot(
                token=self.bot_token,
                channel_id=self.channel_id
            )
            logger.info(f"✅ Telegram бот инициализирован для канала {self.channel_id}")
            
            # Инициализация репортера статистики
            logger.info("📈 Инициализация репортера статистики...")
            self.stats_reporter = StatsReporter(self.telegram_bot, self.predictor)
            logger.info("✅ StatsReporter инициализирован")
            
            # Словарь для отслеживания голов по таймам
            self.match_goals = {}
            
            # Создаем event loop для асинхронных операций
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Флаги состояния
            self.running = False
            self.monitoring_thread = None
            
            # Статистика работы
            self.stats = {
                'matches_analyzed': 0,
                'signals_sent': 0,
                'start_time': datetime.now(),
                'last_check': None,
                'errors_count': 0,
                'api_calls': 0
            }
            
            logger.info("=" * 50)
            logger.info("✅ FootballApp успешно инициализирован")
            logger.info("=" * 50)
            
            # Выводим начальную статистику
            self._log_initial_stats()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации FootballApp: {e}", exc_info=True)
            raise
    
    def _log_initial_stats(self):
        """Логирует начальную статистику"""
        try:
            predictor_stats = self.predictor.get_statistics()
            logger.info(f"📊 Статистика предиктора:")
            logger.info(f"   - Всего предсказаний: {predictor_stats.get('total_predictions', 0)}")
            logger.info(f"   - Отправлено сигналов: {self.stats.get('signals_sent', 0)}")
            logger.info(f"   - Текущие веса: {predictor_stats.get('current_weights', {})}")
            logger.info(f"   - Пороги уверенности: {self.predictor.thresholds}")
            
            if hasattr(self.predictor, 'accuracy_stats'):
                accuracy = self.predictor.accuracy_stats
                logger.info(f"📊 Статистика точности:")
                logger.info(f"   - Всего сигналов: {accuracy.get('total_signals', 0)}")
                logger.info(f"   - Точность: {accuracy.get('accuracy_rate', 0)*100:.1f}%")
            else:
                logger.info("📊 Статистика точности будет доступна после накопления данных")
            
        except Exception as e:
            logger.error(f"Ошибка при логировании начальной статистики: {e}")
    
    def start_monitoring(self):
        """Запускает фоновый мониторинг матчей"""
        if self.running:
            logger.warning("⚠️ Мониторинг уже запущен")
            return
        
        logger.info(f"🔄 Запуск фонового мониторинга (интервал: {self.check_interval}с)...")
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"✅ Фоновый мониторинг запущен")
    
    def stop_monitoring(self):
        """Останавливает фоновый мониторинг"""
        if not self.running:
            logger.warning("⚠️ Мониторинг не был запущен")
            return
        
        logger.info("⏹ Остановка мониторинга...")
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if hasattr(self, 'loop') and self.loop:
            self.loop.close()
        
        logger.info("✅ Мониторинг остановлен")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🔄 Цикл мониторинга запущен")
        
        while self.running:
            try:
                self.loop.run_until_complete(self._check_live_matches_async())
                
                self.stats['last_check'] = datetime.now()
                self.stats['api_calls'] += 1
                
                current_minute = datetime.now().minute
                if current_minute == 0:
                    self._log_statistics()
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}", exc_info=True)
            
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info("⏹ Цикл мониторинга завершен")
    
    def _check_goal_scored(self, match):
        """Проверяет, был ли забит гол в матче"""
        match_id = match.id
        
        if match_id not in self.match_goals:
            self.match_goals[match_id] = {
                'last_score': f"{match.home_score or 0}:{match.away_score or 0}",
                'first_half_goals': 0,
                'second_half_goals': 0,
                'last_check': datetime.now()
            }
            return
        
        last_score = self.match_goals[match_id]['last_score']
        current_score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        if last_score != current_score:
            # Гол забит!
            half = "first" if match.minute and match.minute < 45 else "second"
            self.match_goals[match_id][f'{half}_half_goals'] += 1
            self.match_goals[match_id]['last_score'] = current_score
            self.match_goals[match_id]['last_check'] = datetime.now()
            
            logger.info(f"⚽ ГОЛ в матче {match_id}! {last_score} -> {current_score} ({half} half)")
            
            # Передаем информацию о голе в predictor
            if hasattr(self.predictor, 'check_goal_scored'):
                self.predictor.check_goal_scored(match)
    
    def _create_match_analysis(self, match, signal) -> MatchAnalysis:
        """Создает объект MatchAnalysis из сигнала"""
        
        # Создаем LiveStats с базовыми значениями
        stats = LiveStats(
            minute=match.minute or 0,
            shots_home=signal.get('stats', {}).get('home', {}).get('shots', 0),
            shots_away=signal.get('stats', {}).get('away', {}).get('shots', 0),
            shots_ontarget_home=signal.get('stats', {}).get('home', {}).get('shots_on_target', 0),
            shots_ontarget_away=signal.get('stats', {}).get('away', {}).get('shots_on_target', 0),
            possession_home=signal.get('stats', {}).get('home', {}).get('possession', 50),
            possession_away=signal.get('stats', {}).get('away', {}).get('possession', 50),
            corners_home=signal.get('stats', {}).get('home', {}).get('corners', 0),
            corners_away=signal.get('stats', {}).get('away', {}).get('corners', 0),
            fouls_home=0,
            fouls_away=0,
            yellow_cards_home=0,
            yellow_cards_away=0,
            dangerous_attacks_home=signal.get('stats', {}).get('home', {}).get('dangerous_attacks', 0),
            dangerous_attacks_away=signal.get('stats', {}).get('away', {}).get('dangerous_attacks', 0),
            passes_home=0,
            passes_away=0,
            passes_accuracy_home=0,
            passes_accuracy_away=0
        )
        
        # Создаем GoalSignal
        goal_signal = GoalSignal(
            match_id=match.id,
            predicted_minute=match.minute or 0,
            probability=signal.get('probability', 0) * 100,
            signal_type=signal.get('confidence', 'MEDIUM'),
            description=f"Вероятность гола {signal.get('probability', 0)*100:.1f}%",
            timestamp=datetime.now(),
            stats=stats.to_dict(),
            minutes_left=90 - (match.minute or 0),
            xg_data=None
        )
        
        # Создаем MatchAnalysis
        analysis = MatchAnalysis(
            match_id=match.id,
            timestamp=datetime.now(),
            minute=match.minute or 0,
            score=f"{match.home_score or 0}:{match.away_score or 0}",
            stats=stats,
            activity_level="HIGH",
            activity_description="Активный матч",
            attack_potential="HIGH",
            next_signal=goal_signal,
            has_signal=True,
            xg_data=None
        )
        
        return analysis
    
    def _format_signal_message(self, match, signal) -> str:
        """Форматирует сигнал для отправки в Telegram с полной статистикой"""
        home_team = match.home_team.name if match.home_team else "Home"
        away_team = match.away_team.name if match.away_team else "Away"
        
        confidence = signal.get('confidence', 'MEDIUM')
        confidence_emojis = {
            "VERY_HIGH": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "VERY_LOW": "⚪"
        }
        emoji = confidence_emojis.get(confidence, "⚪")
        
        # Текущий счет
        current_score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        # Ссылка на матч
        match_url = signal.get('match_url', 'https://www.sofascore.com')
        
        # Определяем период матча
        period = ""
        if match.minute:
            if match.minute < 45:
                period = "1-й тайм"
            elif match.minute < 90:
                period = "2-й тайм"
            else:
                period = "Доп. время"
        
        # Получаем статистику
        home_stats = signal.get('stats', {}).get('home', {})
        away_stats = signal.get('stats', {}).get('away', {})
        
        # Получаем форму команд
        home_form = signal.get('form', {}).get('home', {})
        away_form = signal.get('form', {}).get('away', {})
        
        # Проверяем, есть ли реальная статистика
        has_stats = any([
            home_stats.get('shots', 0) > 0,
            away_stats.get('shots', 0) > 0,
            home_stats.get('shots_on_target', 0) > 0,
            away_stats.get('shots_on_target', 0) > 0,
            home_stats.get('corners', 0) > 0,
            away_stats.get('corners', 0) > 0
        ])
        
        # Формируем сообщение
        message_lines = [
            f"{emoji} **Потенциальный гол!**",
            f"⚔️ **{home_team} vs {away_team}**",
            f"📊 **Счет:** {current_score}",
            f"⏱ **Минута:** {match.minute or 0}' {period}",
            "",
            f"📈 **Вероятность гола:** {signal.get('probability', 0)*100:.1f}%",
            f"🎯 **Уверенность:** {confidence}",
            "",
            f"🏠 **{home_team}:** {signal.get('home_prob', 0)*100:.1f}%",
            f"✈️ **{away_team}:** {signal.get('away_prob', 0)*100:.1f}%",
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
                f"  • Опасные атаки: {home_stats.get('dangerous_attacks', 0)} : {away_stats.get('dangerous_attacks', 0)}",
            ])
        else:
            message_lines.extend([
                "",
                "📊 **СТАТИСТИКА МАТЧА:**",
                "  • Статистика временно недоступна"
            ])
        
        # Добавляем форму команд если она есть
        if home_form or away_form:
            message_lines.extend([
                "",
                "📈 **ФОРМА КОМАНД:**",
            ])
            
            if home_form:
                form_string = home_form.get('form_string', '')
                ppg = home_form.get('points_per_game', 0)
                if form_string:
                    message_lines.append(f"  • {home_team}: {form_string} ({ppg:.1f} о/м)")
                else:
                    message_lines.append(f"  • {home_team}: нет данных")
            
            if away_form:
                form_string = away_form.get('form_string', '')
                ppg = away_form.get('points_per_game', 0)
                if form_string:
                    message_lines.append(f"  • {away_team}: {form_string} ({ppg:.1f} о/м)")
                else:
                    message_lines.append(f"  • {away_team}: нет данных")
        
        # Добавляем информацию о голах в таймах
        match_id = match.id
        if match_id in self.match_goals:
            first_half = self.match_goals[match_id].get('first_half_goals', 0)
            second_half = self.match_goals[match_id].get('second_half_goals', 0)
            if first_half > 0 or second_half > 0:
                message_lines.extend([
                    "",
                    f"⚽ **ГОЛЫ ПО ТАЙМАМ:**",
                    f"  • 1-й тайм: {first_half}",
                    f"  • 2-й тайм: {second_half}"
                ])
        
        message_lines.extend([
            "",
            f"🔗 **Смотреть матч:** {match_url}"
        ])
        
        return "\n".join(message_lines)
    
    async def _check_live_matches_async(self):
        """Асинхронно проверяет live-матчи и генерирует сигналы"""
        try:
            logger.debug("🔍 Запрос live-матчей...")
            matches = await self.api_client.get_live_matches()
            
            if not matches:
                logger.debug("ℹ️ Нет live-матчей для анализа")
                return
            
            # Фильтруем матчи с крупным счетом
            filtered_matches = []
            for match in matches:
                home_score = match.home_score or 0
                away_score = match.away_score or 0
                
                if abs(home_score - away_score) >= 3:
                    logger.debug(f"Пропускаем матч {match.id}: крупный счет {home_score}:{away_score}")
                    continue
                
                if home_score >= 4 or away_score >= 4:
                    logger.debug(f"Пропускаем матч {match.id}: много голов {home_score}:{away_score}")
                    continue
                
                filtered_matches.append(match)
            
            logger.info(f"📊 Найдено {len(matches)} матчей, после фильтрации: {len(filtered_matches)}")
            
            signals_generated = 0
            telegram_queue = 0
            
            for match in filtered_matches:
                try:
                    if not match or not hasattr(match, 'id'):
                        continue
                    
                    # Проверяем, изменился ли счет (был ли гол)
                    self._check_goal_scored(match)
                    
                    home_team = match.home_team.name if match.home_team else "Unknown"
                    away_team = match.away_team.name if match.away_team else "Unknown"
                    
                    logger.debug(f"⚽ Анализ матча: {home_team} vs {away_team} (ID: {match.id}, минута: {match.minute}, счет: {match.home_score}:{match.away_score})")
                    
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        # Создаем объект MatchAnalysis
                        analysis = self._create_match_analysis(match, signal)
                        
                        # Форматируем сообщение
                        formatted_message = self._format_signal_message(match, signal)
                        
                        # Для отладки - выводим сообщение в лог
                        logger.debug(f"📨 Сообщение для отправки (первые 100 символов): {formatted_message[:100]}...")
                        
                        # Отправляем сигнал через Telegram бота
                        if self.telegram_bot.send_goal_signal(match, analysis, formatted_message):
                            signals_generated += 1
                            self.stats['signals_sent'] += 1
                            
                            # Проверяем статус отправки
                            queue_size = self.telegram_bot.get_queue_size()
                            if queue_size > 0:
                                telegram_queue = queue_size
                            
                            logger.info(f"📨 Сигнал сгенерирован для матча {match.id}: "
                                       f"{home_team} vs {away_team} - "
                                       f"счет {match.home_score or 0}:{match.away_score or 0}, "
                                       f"вероятность {signal.get('probability', 0)*100:.1f}%")
                            
                            if match.is_finished and hasattr(self, 'team_analyzer'):
                                self._save_match_to_history(match)
                                
                                # Проверяем точность прогноза
                                if hasattr(self, 'stats_reporter'):
                                    self.stats_reporter.check_prediction_accuracy(match, signal)
                        else:
                            logger.debug(f"⏳ Сигнал для матча {match.id} поставлен в очередь")
                    
                    self.stats['matches_analyzed'] += 1
                    
                except Exception as e:
                    self.stats['errors_count'] += 1
                    logger.error(f"❌ Ошибка при анализе матча {getattr(match, 'id', 'unknown')}: {e}")
            
            if signals_generated > 0:
                queue_size = self.telegram_bot.get_queue_size()
                logger.info(f"📊 Всего сгенерировано сигналов: {signals_generated}, в очереди: {queue_size}")
                
                # Если очередь большая, логируем предупреждение
                if queue_size > 10:
                    logger.warning(f"⚠️ Большая очередь Telegram: {queue_size} сообщений")
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"❌ Ошибка получения live-матчей: {e}", exc_info=True)
    
    def _save_match_to_history(self, match):
        """Сохраняет завершенный матч в историю"""
        try:
            if not match or not match.is_finished:
                return
            
            if not match.home_team or not match.away_team:
                logger.warning(f"⚠️ Нет данных о командах для матча {match.id}")
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
            
            logger.info(f"📊 Матч {match.id} сохранен в историю")
            
            if hasattr(self.predictor, 'update_accuracy'):
                total_goals = (match.home_score or 0) + (match.away_score or 0)
                self.predictor.update_accuracy(str(match.id), total_goals)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения матча {match.id} в историю: {e}")
    
    def analyze_single_match(self, match_id: int) -> Optional[Dict]:
        """Анализирует конкретный матч по ID"""
        try:
            logger.info(f"🔍 Анализ матча по ID: {match_id}")
            
            match = self.loop.run_until_complete(
                self.api_client.get_match_by_id(match_id)
            )
            
            if not match:
                logger.warning(f"⚠️ Матч {match_id} не найден")
                return None
            
            home_team = match.home_team.name if match.home_team else "Unknown"
            away_team = match.away_team.name if match.away_team else "Unknown"
            
            logger.info(f"⚽ Анализ матча: {home_team} vs {away_team}")
            
            prediction = self.predictor.predict_match(match)
            
            if prediction:
                probability = prediction.get('total_goal_probability', 0) * 100
                confidence = prediction.get('confidence_level', 'UNKNOWN')
                
                logger.info(f"✅ Матч {match_id} проанализирован:")
                logger.info(f"   - Вероятность гола: {probability:.1f}%")
                logger.info(f"   - Уверенность: {confidence}")
            
            return prediction
            
        except Exception as e:
            self.stats['errors_count'] += 1
            logger.error(f"❌ Ошибка при анализе матча {match_id}: {e}", exc_info=True)
            return None
    
    def _log_statistics(self):
        """Логирует подробную статистику работы"""
        runtime = datetime.now() - self.stats['start_time']
        hours = runtime.total_seconds() / 3600
        minutes = runtime.total_seconds() / 60
        
        predictor_stats = self.predictor.get_statistics()
        telegram_stats = self.telegram_bot.get_stats() if hasattr(self.telegram_bot, 'get_stats') else {}
        
        log_message = [
            "\n" + "="*60,
            "📊 СТАТИСТИКА РАБОТЫ ПРИЛОЖЕНИЯ",
            "="*60,
            f"⏱ Время работы: {int(hours)}ч {int(minutes % 60)}мин",
            f"📈 Проанализировано матчей: {self.stats['matches_analyzed']}",
            f"📨 Отправлено сигналов: {self.stats['signals_sent']}",
            f"🔁 Вызовов API: {self.stats['api_calls']}",
            f"❌ Ошибок: {self.stats['errors_count']}",
            f"📤 Размер очереди Telegram: {self.telegram_bot.get_queue_size()}",
            f"📤 Успешно отправлено: {telegram_stats.get('successful_sends', 0)}",
            f"📤 Всего сигналов в памяти: {telegram_stats.get('sent_signals', 0)}",
            f"📤 Неудачных попыток: {telegram_stats.get('failed_attempts', 0)}",
            "-"*60,
            "📊 СТАТИСТИКА ПРЕДИКТОРА",
            f"   Всего предсказаний: {predictor_stats.get('total_predictions', 0)}",
            f"   Средняя вероятность: {predictor_stats.get('avg_probability', 0)*100:.1f}%",
            f"   Текущие веса: {predictor_stats.get('current_weights', {})}",
            f"   Пороги: {self.predictor.thresholds}"
        ]
        
        if hasattr(self.predictor, 'accuracy_stats'):
            accuracy = self.predictor.accuracy_stats
            if accuracy.get('total_signals', 0) > 0:
                log_message.extend([
                    "-"*60,
                    "📊 СТАТИСТИКА ТОЧНОСТИ",
                    f"   Всего сигналов: {accuracy.get('total_signals', 0)}",
                    f"   Точность: {accuracy.get('accuracy_rate', 0)*100:.1f}%",
                    f"   По уровням:"
                ])
                
                # Добавляем статистику по уровням уверенности
                by_confidence = accuracy.get('by_confidence', {})
                for level, data in by_confidence.items():
                    if data.get('total', 0) > 0:
                        level_acc = (data.get('correct', 0) / data.get('total', 1)) * 100
                        log_message.append(f"      {level}: {data.get('total', 0)} прогнозов, точность {level_acc:.1f}%")
        
        log_message.append("="*60)
        logger.info("\n".join(log_message))
        
        self._save_stats_to_file()
    
    def _save_stats_to_file(self):
        """Сохраняет статистику в файл"""
        try:
            os.makedirs('stats', exist_ok=True)
            filename = f"stats/stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Статистика работы на {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n")
                f.write(f"Проанализировано матчей: {self.stats['matches_analyzed']}\n")
                f.write(f"Отправлено сигналов: {self.stats['signals_sent']}\n")
                f.write(f"Вызовов API: {self.stats['api_calls']}\n")
                f.write(f"Ошибок: {self.stats['errors_count']}\n")
                f.write(f"Размер очереди Telegram: {self.telegram_bot.get_queue_size()}\n")
                
                telegram_stats = self.telegram_bot.get_stats() if hasattr(self.telegram_bot, 'get_stats') else {}
                f.write(f"Успешно отправлено: {telegram_stats.get('successful_sends', 0)}\n")
                f.write(f"Всего сигналов в памяти: {telegram_stats.get('sent_signals', 0)}\n")
                f.write(f"Неудачных попыток: {telegram_stats.get('failed_attempts', 0)}\n")
                
                if hasattr(self.predictor, 'accuracy_stats'):
                    accuracy = self.predictor.accuracy_stats
                    f.write(f"\nТочность прогнозов: {accuracy.get('accuracy_rate', 0)*100:.1f}%\n")
                    
                    by_confidence = accuracy.get('by_confidence', {})
                    f.write("\nСтатистика по уровням уверенности:\n")
                    for level, data in by_confidence.items():
                        if data.get('total', 0) > 0:
                            level_acc = (data.get('correct', 0) / data.get('total', 1)) * 100
                            f.write(f"  {level}: {data.get('total', 0)} прогнозов, точность {level_acc:.1f}%\n")
                
                predictor_stats = self.predictor.get_statistics()
                f.write(f"\nТекущие веса: {predictor_stats.get('current_weights', {})}\n")
                f.write(f"Пороги уверенности: {self.predictor.thresholds}\n")
            
            logger.info(f"💾 Статистика сохранена в {filename}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения статистики: {e}")
    
    def get_status(self) -> Dict:
        """Возвращает текущий статус приложения"""
        runtime = datetime.now() - self.stats['start_time']
        
        status = {
            'running': self.running,
            'uptime_seconds': runtime.total_seconds(),
            'uptime_formatted': str(runtime).split('.')[0],
            'stats': self.stats.copy(),
            'predictor_stats': self.predictor.get_statistics(),
            'telegram_queue_size': self.telegram_bot.get_queue_size(),
            'telegram_stats': self.telegram_bot.get_stats() if hasattr(self.telegram_bot, 'get_stats') else {},
            'thresholds': self.predictor.thresholds,
            'timestamp': datetime.now().isoformat()
        }
        
        if hasattr(self.predictor, 'accuracy_stats'):
            status['accuracy_stats'] = self.predictor.accuracy_stats.copy()
        
        return status
    
    def cleanup(self):
        """Очистка ресурсов перед завершением"""
        logger.info("🧹 Очистка ресурсов...")
        
        self.stop_monitoring()
        self._log_statistics()
        
        try:
            self.predictor.save_predictions()
            logger.info("✅ История предсказаний сохранена")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения истории предсказаний: {e}")
        
        # Сохраняем статистику репортера
        if hasattr(self, 'stats_reporter'):
            self.stats_reporter.save_stats()
            logger.info("✅ Статистика репортера сохранена")
        
        # Очищаем старые сигналы в Telegram боте
        if hasattr(self, 'telegram_bot') and hasattr(self.telegram_bot, 'clear_old_signals'):
            self.telegram_bot.clear_old_signals()
            logger.info("✅ Старые сигналы очищены")
        
        logger.info("✅ Очистка завершена")