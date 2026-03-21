import logging
import threading
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
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
    """Быстрая версия приложения с оптимизациями"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("🚀 Запуск быстрой версии FootballApp...")
        logger.info("=" * 50)
        
        try:
            self.bot_token = config.TELEGRAM_TOKEN
            self.channel_id = config.CHANNEL_ID
            self.check_interval = 30
            
            if not self.bot_token:
                raise ValueError("TELEGRAM_TOKEN not found in config")
            
            logger.info("📡 Быстрое подключение к API...")
            self.api_client = UnifiedFastClient()
            
            logger.info("🧠 Инициализация предиктора...")
            self.predictor = Predictor()
            
            logger.info("📊 Инициализация анализатора формы...")
            self.team_analyzer = TeamFormAnalyzer()
            
            logger.info("📈 Инициализация репортера статистики...")
            self.stats_reporter = StatsReporter(None, self.predictor)
            
            logger.info("🤖 Инициализация Telegram бота...")
            self.telegram_bot = TelegramBot(self.bot_token, self.channel_id)
            
            self.stats_reporter.telegram_bot = self.telegram_bot
            
            self.match_goals = {}
            self.last_predictions = {}
            self.running = False
            self.monitoring_thread = None
            self.last_update_time = datetime.now()
            
            self.stats = {
                'matches_analyzed': 0,
                'signals_sent': 0,
                'start_time': datetime.now(),
                'last_check': None,
                'errors_count': 0,
                'api_calls': 0,
                'last_alive': datetime.now().isoformat()
            }
            
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("✅ Быстрая инициализация завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        logger.info(f"📡 Получен сигнал {signum}, завершаем работу...")
        self.stop_monitoring()
        self.cleanup()
        sys.exit(0)
    
    def start_monitoring(self):
        if self.running:
            return
        logger.info(f"🔄 Запуск быстрого мониторинга (интервал: {self.check_interval}с)")
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._fast_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏹ Мониторинг остановлен")
    
    def _fast_loop(self):
        logger.info("🔄 Быстрый цикл запущен")
        
        while self.running:
            loop_start = time.time()
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._fast_check())
                loop.close()
                
                self.stats['last_check'] = datetime.now()
                self.stats['api_calls'] += 1
                self.last_update_time = datetime.now()
                self.stats['last_alive'] = datetime.now().isoformat()
                
            except Exception as e:
                self.stats['errors_count'] += 1
                logger.error(f"❌ Ошибка в цикле: {e}")
            
            loop_duration = time.time() - loop_start
            logger.info(f"⏱ Цикл выполнен за {loop_duration:.1f}с")
            
            sleep_time = max(1, self.check_interval - loop_duration)
            logger.info(f"💤 Следующая проверка через {sleep_time:.0f}с")
            
            for _ in range(int(sleep_time)):
                if not self.running:
                    break
                time.sleep(1)
    
    async def _fast_check(self):
        """Быстрая асинхронная проверка матчей"""
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка live матчей...")
            
            # Принудительное обновление кэша каждые 3 цикла
            if self.stats['api_calls'] % 3 == 0 and self.stats['api_calls'] > 0:
                logger.info("🔄 Принудительная очистка кэша API")
                if hasattr(self.api_client, 'sstats'):
                    self.api_client.sstats.cache = {}
            
            matches = await self.api_client.get_live_matches()
            
            if not matches:
                logger.warning(f"📭 Нет live матчей, повторная попытка через 5 секунд")
                await asyncio.sleep(5)
                # Принудительно очищаем кэш API
                if hasattr(self.api_client, 'sstats'):
                    self.api_client.sstats.cache = {}
                return
            
            logger.info(f"📊 Получено {len(matches)} матчей")
            
            filtered = [m for m in matches if self._quick_filter(m)]
            
            if filtered:
                logger.info(f"📊 Анализ {len(filtered)} матчей из {len(matches)}")
            
            for match in filtered:
                try:
                    # Получаем статистику
                    stats = await self.api_client.get_match_statistics(match)
                    if stats:
                        match.stats = stats
                    
                    signal = self.predictor.analyze_live_match(match)
                    
                    if signal:
                        self.last_predictions[match.id] = signal
                        self.stats_reporter.register_prediction(match.id, signal, match)
                        
                        # Получаем сообщение
                        message = signal.get('message')
                        if message:
                            # Отправляем в Telegram
                            self.telegram_bot.send_message(message)
                            self.stats['signals_sent'] += 1
                            logger.info(f"📨 Сигнал отправлен: {match.home_team.name} vs {match.away_team.name}")
                        else:
                            logger.warning(f"⚠️ Сигнал без сообщения для матча {match.id}")
                    
                    self.stats['matches_analyzed'] += 1
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    self.stats['errors_count'] += 1
                    logger.error(f"❌ Ошибка матча {getattr(match, 'id', 'unknown')}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки: {e}")
            await asyncio.sleep(5)
    
    def _quick_filter(self, match) -> bool:
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
    
    def cleanup(self):
        logger.info("🧹 Очистка...")
        self.stop_monitoring()
        
        if hasattr(self.api_client, 'close'):
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.api_client.close())
                loop.close()
            except:
                pass
        
        if hasattr(self.telegram_bot, 'stop'):
            self.telegram_bot.stop()
        
        self.predictor.save_predictions()
        logger.info("✅ Очистка завершена")