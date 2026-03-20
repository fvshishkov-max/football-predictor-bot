import logging
import threading
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import os
import time
import signal
import sys

import config
from api_client import UnifiedFastClient
from predictor import Predictor
from telegram_bot_ultimate import TelegramBot
from team_form import TeamFormAnalyzer
from stats_reporter import StatsReporter

logger = logging.getLogger(__name__)

class FastFootballApp:
    """Быстрая версия приложения с оптимизированными таймаутами"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("🚀 Запуск быстрой версии FootballApp...")
        logger.info("=" * 50)
        
        try:
            self.bot_token = config.TELEGRAM_TOKEN
            self.channel_id = config.CHANNEL_ID
            self.check_interval = 60  # Фиксируем 60 секунд
            
            if not self.bot_token:
                raise ValueError("TELEGRAM_TOKEN not found in config")
            
            logger.info("📡 Быстрое подключение к API...")
            self.api_client = UnifiedFastClient()
            
            logger.info("🧠 Инициализация предиктора...")
            self.predictor = Predictor()
            
            logger.info("📊 Инициализация анализатора формы...")
            self.team_analyzer = TeamFormAnalyzer()
            
            logger.info("📈 Инициализация репортера статистики...")
            self.stats_reporter = StatsReporter(None, self.predictor)  # Сначала без telegram_bot
            
            logger.info("🤖 Инициализация Telegram бота...")
            self.telegram_bot = TelegramBot(
                self.bot_token, 
                self.channel_id
                # Убрали predictor и stats_reporter - они не нужны для простой версии
)
            
            # Обновляем stats_reporter с telegram_bot
            self.stats_reporter.telegram_bot = self.telegram_bot
            
            self.match_goals = {}
            self.last_predictions = {}
            self.running = False
            self.monitoring_thread = None
            self.last_update_time = datetime.now()
            self.update_count = 0
            self.no_update_counter = 0
            self.consecutive_timeouts = 0
            
            self.stats = {
                'matches_analyzed': 0,
                'signals_sent': 0,
                'start_time': datetime.now(),
                'last_check': None,
                'errors_count': 0,
                'api_calls': 0,
                'timeouts': 0
            }
            
            # Настраиваем обработчик сигналов
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("✅ Быстрая инициализация завершена")
            self._log_initial_stats()
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"📡 Получен сигнал {signum}, завершаем работу...")
        self.stop_monitoring()
        self.cleanup()
        sys.exit(0)
    
    def _log_initial_stats(self):
        """Быстрое логирование статистики"""
        stats = self.predictor.get_statistics()
        logger.info(f"📊 Статистика: предсказаний {stats.get('total_predictions', 0)}")
    
    def start_monitoring(self):
        """Запускает быстрый мониторинг"""
        if self.running:
            return
        
        logger.info(f"🔄 Запуск быстрого мониторинга (интервал: {self.check_interval}с)")
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._fast_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Запускаем поток для мониторинга зависаний
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏹ Мониторинг остановлен")
    
    def _watchdog_loop(self):
        """Сторожевой таймер для обнаружения зависаний"""
        while self.running:
            time.sleep(60)  # Проверяем каждую минуту
            
            time_since_update = (datetime.now() - self.last_update_time).total_seconds()
            
            if time_since_update > 900:  # 15 минут без обновлений
                logger.warning(f"⚠️ Сторожевой таймер: нет обновлений {time_since_update:.0f}с")
                self.no_update_counter += 1
                
                if self.no_update_counter >= 2:  # 30 минут без обновлений
                    logger.error("❌ Обнаружено зависание! Перезапускаем цикл...")
                    self._restart_loop()
                    self.no_update_counter = 0
            else:
                self.no_update_counter = 0
    
    def _restart_loop(self):
        """Перезапускает цикл мониторинга"""
        logger.info("🔄 Перезапуск цикла мониторинга...")
        
        # Останавливаем старый поток
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        # Запускаем новый
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._fast_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("✅ Цикл перезапущен")
    
    def _fast_loop(self):
        """Быстрый цикл с частыми проверками"""
        logger.info("🔄 Быстрый цикл запущен (проверка каждую минуту)")
        
        while self.running:
            loop_start = time.time()
            
            try:
                # Создаем новый event loop для каждого цикла
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Запускаем проверку
                try:
                    loop.run_until_complete(self._fast_check())
                    self.consecutive_timeouts = 0
                except Exception as e:
                    logger.error(f"❌ Ошибка в _fast_check: {e}")
                    self.consecutive_timeouts += 1
                finally:
                    loop.close()
                
                self.stats['last_check'] = datetime.now()
                self.stats['api_calls'] += 1
                self.last_update_time = datetime.now()
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"❌ Ошибка в цикле: {e}")
            
            # Вычисляем время выполнения
            loop_duration = time.time() - loop_start
            logger.info(f"⏱ Цикл выполнен за {loop_duration:.1f}с")
            
            # Определяем время сна до следующей проверки
            sleep_time = 60  # Всегда 60 секунд
            
            # Если были ошибки, ждем меньше
            if self.consecutive_timeouts > 3:
                sleep_time = 30
                logger.warning(f"⚠️ Много ошибок, следующая проверка через {sleep_time}с")
            
            logger.info(f"💤 Следующая проверка через {sleep_time}с")
            
            # Постепенный сон с проверкой флага running
            for _ in range(sleep_time):
                if not self.running:
                    break
                time.sleep(1)
    
    async def _fast_check(self):
        """Быстрая асинхронная проверка матчей"""
        try:
            # Получаем матчи
            logger.debug("📡 Запрос live матчей...")
            matches = await self.api_client.get_live_matches()
            
            if not matches:
                logger.debug("📭 Нет live матчей")
                return
            
            logger.info(f"📊 Получено {len(matches)} матчей")
            
            # Быстрая фильтрация
            filtered = [m for m in matches if self._quick_filter(m)]
            
            if filtered:
                logger.info(f"📊 Анализ {len(filtered)} матчей из {len(matches)}")
            else:
                logger.debug(f"📭 Нет подходящих матчей для анализа")
                return
            
            for match in filtered:
                try:
                    self._check_goal_fast(match)
                    
                    # Получаем статистику
                    logger.debug(f"📊 Запрос статистики для матча {match.id}")
                    stats = await self.api_client.get_match_statistics(match)
                    
                    if stats:
                        match.stats = stats
                        logger.debug(f"✅ Статистика получена для матча {match.id}")
                    
                    # Анализируем матч
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        self.last_predictions[match.id] = signal
                        self.stats_reporter.register_prediction(match.id, signal, match)
                        
                        # Получаем сообщение
                        message = None
                        if isinstance(signal, dict):
                            message = signal.get('message')
                        
                        if message is None:
                            home_name = match.home_team.name if match.home_team else "Unknown"
                            away_name = match.away_team.name if match.away_team else "Unknown"
                            prob = signal.get('probability', 0) * 100 if isinstance(signal, dict) else 0
                            message = f"⚽ {home_name} vs {away_name} - {prob:.1f}%"
                        
                        # Отправляем сигнал
                        try:
                            if self.telegram_bot.send_goal_signal(match, None, message):
                                self.stats['signals_sent'] += 1
                                logger.info(f"📨 Сигнал: {match.home_team.name} vs {match.away_team.name} - {signal.get('probability', 0)*100:.1f}%")
                        except Exception as e:
                            logger.error(f"❌ Ошибка отправки сигнала: {e}")
                    
                    self.stats['matches_analyzed'] += 1
                    
                    # Небольшая пауза между матчами
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.stats['errors_count'] += 1
                    logger.error(f"❌ Ошибка матча {getattr(match, 'id', 'unknown')}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {e}")
    
    def _quick_filter(self, match) -> bool:
        """Быстрая фильтрация матчей"""
        if match.minute and match.minute > 75:
            return False
        if abs((match.home_score or 0) - (match.away_score or 0)) >= 3:
            return False
        if (match.home_score or 0) >= 4 or (match.away_score or 0) >= 4:
            return False
        return True
    
    def _check_goal_fast(self, match):
        """Быстрая проверка гола"""
        match_id = match.id
        current = f"{match.home_score or 0}:{match.away_score or 0}"
        
        if match_id not in self.match_goals:
            self.match_goals[match_id] = {
                'last': current,
                'first': 0,
                'second': 0
            }
            return
        
        if self.match_goals[match_id]['last'] != current:
            half = "second" if match.minute and match.minute >= 45 else "first"
            self.match_goals[match_id][half] += 1
            self.match_goals[match_id]['last'] = current
            logger.info(f"⚽ ГОЛ! {match_id} - {current}")
            
            if match_id in self.last_predictions:
                self.stats_reporter.check_goal_scored(match, self.last_predictions[match_id])
    
    def cleanup(self):
            """Быстрая очистка"""
            logger.info("🧹 Очистка...")
            self.stop_monitoring()
            
            if hasattr(self.stats_reporter, 'stop'):
                self.stats_reporter.stop()
            
            if hasattr(self.api_client, 'close'):
                try:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(asyncio.wait_for(self.api_client.close(), timeout=5))
                    loop.close()
                except:
                    pass
            
            if hasattr(self.telegram_bot, 'stop'):
                self.telegram_bot.stop()
            
            self.predictor.save_predictions()
            logger.info("✅ Очистка завершена")