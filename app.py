import logging
import threading
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import os

import config
from api_client import UnifiedFastClient
from predictor import Predictor
from telegram_bot import TelegramBot
from team_form import TeamFormAnalyzer
from stats_reporter import StatsReporter

logger = logging.getLogger(__name__)

class FastFootballApp:
    """Быстрая версия приложения с оптимизациями"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("🚀 Запуск быстрой версии FootballApp...")
        logger.info("=" * 50)
        
        try:
            self.bot_token = config.TELEGRAM_TOKEN
            self.channel_id = config.CHANNEL_ID
            self.check_interval = config.CHECK_INTERVAL
            
            if not self.bot_token:
                raise ValueError("TELEGRAM_TOKEN not found in config")
            
            logger.info("📡 Быстрое подключение к API...")
            self.api_client = UnifiedFastClient()
            
            logger.info("🧠 Инициализация предиктора...")
            self.predictor = Predictor()
            
            logger.info("📊 Инициализация анализатора формы...")
            self.team_analyzer = TeamFormAnalyzer()
            
            logger.info("🤖 Инициализация Telegram бота...")
            self.telegram_bot = TelegramBot(self.bot_token, self.channel_id)
            
            logger.info("📈 Инициализация репортера статистики...")
            self.stats_reporter = StatsReporter(self.telegram_bot, self.predictor)
            
            self.match_goals = {}
            self.last_predictions = {}
            self.running = False
            self.monitoring_thread = None
            
            self.stats = {
                'matches_analyzed': 0,
                'signals_sent': 0,
                'start_time': datetime.now(),
                'last_check': None,
                'errors_count': 0,
                'api_calls': 0
            }
            
            logger.info("✅ Быстрая инициализация завершена")
            self._log_initial_stats()
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
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
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logger.info("⏹ Мониторинг остановлен")
    
    def _fast_loop(self):
        """Быстрый цикл без лишних задержек"""
        logger.info("🔄 Быстрый цикл запущен")
        
        while self.running:
            try:
                # Быстрый запуск асинхронной проверки
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._fast_check())
                loop.close()
                
                self.stats['last_check'] = datetime.now()
                self.stats['api_calls'] += 1
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"❌ Ошибка в цикле: {e}")
            
            # Минимальная задержка
            for _ in range(self.check_interval):
                if not self.running:
                    break
                import time
                time.sleep(1)
    
    async def _fast_check(self):
        """Быстрая асинхронная проверка матчей"""
        try:
            matches = await self.api_client.get_live_matches()
            
            if not matches:
                return
            
            # Быстрая фильтрация
            filtered = [m for m in matches if self._quick_filter(m)]
            
            if filtered:
                logger.info(f"📊 Анализ {len(filtered)} матчей")
            
            for match in filtered:
                try:
                    self._check_goal_fast(match)
                    
                    # Параллельное получение статистики и предсказания
                    stats_task = asyncio.create_task(
                        self.api_client.get_match_statistics(match)
                    )
                    
                    stats = await stats_task
                    if stats:
                        match.stats = stats
                    
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        self.last_predictions[match.id] = signal
                        self.stats_reporter.register_prediction(match.id, signal)
                        
                        # Отправка без лишних проверок
                        if self.telegram_bot.send_goal_signal(match, None, signal['message']):
                            self.stats['signals_sent'] += 1
                            logger.info(f"📨 Сигнал: {match.home_team.name} vs {match.away_team.name} - {signal['probability']*100:.1f}%")
                    
                    self.stats['matches_analyzed'] += 1
                    
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
        
        if hasattr(self.api_client, 'close'):
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.api_client.close())
            loop.close()
        
        self.predictor.save_predictions()
        logger.info("✅ Очистка завершена")