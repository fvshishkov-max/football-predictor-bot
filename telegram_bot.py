# telegram_bot.py
import asyncio
import logging
from telegram import Bot
from telegram.error import TimedOut, RetryAfter, NetworkError
from datetime import datetime
from typing import Optional, Dict
import time
import threading
from queue import Queue

from models import Match, MatchAnalysis

logger = logging.getLogger(__name__)

class TelegramBot:
    """Класс для работы с Telegram ботом с очередью сообщений"""

    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.sent_signals = set()  # Уже отправленные сигналы (глобально)
        self.sent_signals_per_match = {}  # Сигналы по матчам для проверки дублирования
        self.max_retries = 5
        self.retry_delay = 2
        self.message_queue = Queue(maxsize=100)
        self.last_send_time = 0
        self.min_interval = 3  # Уменьшили до 3 секунд
        self.sent_lock = threading.Lock()
        self.failed_attempts = 0
        self.successful_sends = 0
        self.start_queue_processor()
        logger.info(f"🚀 Запущен обработчик очереди Telegram для канала {channel_id}")

    def start_queue_processor(self):
        def process_queue():
            logger.info("🚀 Запущен обработчик очереди Telegram")
            consecutive_failures = 0
            
            while True:
                try:
                    message_data = self.message_queue.get()
                    if message_data is None:
                        break
                    
                    with self.sent_lock:
                        # Проверяем, не отправляли ли уже такой сигнал
                        if message_data['key'] in self.sent_signals:
                            logger.debug(f"⏭️ Сигнал {message_data['key']} уже отправлен глобально")
                            self.message_queue.task_done()
                            continue
                        
                        # Проверяем дублирование для этого матча (не чаще чем раз в 15 минут)
                        match_id = message_data['key'].split('_')[0]
                        current_time = time.time()
                        
                        if match_id in self.sent_signals_per_match:
                            last_signal_time = self.sent_signals_per_match[match_id]
                            if current_time - last_signal_time < 900:  # 15 минут
                                logger.debug(f"⏭️ Пропускаем сигнал для матча {match_id}: слишком часто (прошло {current_time - last_signal_time:.0f}с)")
                                self.message_queue.task_done()
                                continue
                    
                    # Проверяем интервал между сообщениями
                    current_time = time.time()
                    time_since_last = current_time - self.last_send_time
                    if time_since_last < self.min_interval:
                        wait_time = self.min_interval - time_since_last
                        logger.debug(f"⏳ Ожидание {wait_time:.1f} сек перед отправкой")
                        time.sleep(wait_time)
                    
                    # Отправляем сообщение
                    success = self._send_message_sync(message_data['text'])
                    
                    if success:
                        with self.sent_lock:
                            self.sent_signals.add(message_data['key'])
                            match_id = message_data['key'].split('_')[0]
                            self.sent_signals_per_match[match_id] = time.time()
                            self.successful_sends += 1
                            logger.info(f"✅ Сигнал отправлен: {message_data['key']} (всего успешно: {self.successful_sends})")
                        self.last_send_time = time.time()
                        consecutive_failures = 0
                        self.failed_attempts = 0
                    else:
                        consecutive_failures += 1
                        self.failed_attempts += 1
                        logger.error(f"❌ Не удалось отправить {message_data['key']} (попыток: {consecutive_failures})")
                        
                        # Если много ошибок подряд, увеличиваем интервал
                        if consecutive_failures > 3:
                            logger.warning(f"⚠️ Много ошибок подряд ({consecutive_failures}), увеличиваем интервал до 10с")
                            time.sleep(10)
                    
                    self.message_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в обработчике очереди: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=process_queue, name="TelegramQueue", daemon=True)
        thread.start()

    def _send_message_sync(self, text: str) -> bool:
        """Отправляет сообщение синхронно с улучшенной обработкой ошибок"""
        for attempt in range(self.max_retries):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                bot = Bot(token=self.token)
                
                # Отправляем сообщение
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        bot.send_message(
                            chat_id=self.channel_id,
                            text=text
                        ),
                        timeout=30.0  # Увеличили таймаут
                    )
                )
                loop.close()
                
                # Проверяем, что сообщение действительно отправлено
                if result and result.message_id:
                    logger.debug(f"✅ Сообщение отправлено, ID: {result.message_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Сообщение отправлено, но нет подтверждения")
                    return True
                
            except TimedOut:
                wait_time = self.retry_delay * (attempt + 1)
                logger.warning(f"⏰ Таймаут {attempt + 1}/{self.max_retries}, повтор через {wait_time}с")
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    
            except NetworkError as e:
                wait_time = self.retry_delay * (attempt + 2)
                logger.warning(f"🌐 Сетевая ошибка {attempt + 1}/{self.max_retries}: {e}, повтор через {wait_time}с")
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    
            except Exception as e:
                wait_time = self.retry_delay * (attempt + 1)
                logger.warning(f"❌ Ошибка {attempt + 1}/{self.max_retries}: {e}, повтор через {wait_time}с")
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    
            finally:
                try:
                    if 'loop' in locals() and loop.is_running():
                        loop.close()
                except:
                    pass
        
        return False

    def send_goal_signal(self, match: Match, analysis: MatchAnalysis, formatted_message: str) -> bool:
        """Отправляет сигнал о голе с проверкой на дублирование"""
        if not analysis.next_signal:
            return False
        
        # Создаем уникальный ключ для сигнала
        signal_key = f"{match.id}_{analysis.next_signal.predicted_minute}"
        
        with self.sent_lock:
            # Проверяем, не отправляли ли уже такой сигнал
            if signal_key in self.sent_signals:
                logger.debug(f"⏭️ Сигнал {signal_key} уже был отправлен")
                return True
            
            # Проверяем, не отправляли ли сигнал для этого матча в последние 15 минут
            if match.id in self.sent_signals_per_match:
                last_time = self.sent_signals_per_match[match.id]
                time_diff = time.time() - last_time
                if time_diff < 900:  # 15 минут
                    logger.debug(f"⏭️ Сигнал для матча {match.id} уже отправлялся {time_diff:.0f}с назад")
                    return True
        
        # Проверяем размер очереди
        if self.message_queue.qsize() >= 90:
            logger.warning(f"⚠️ Очередь почти полна ({self.message_queue.qsize()}/100)")
            if self.message_queue.qsize() >= 100:
                logger.error("❌ Очередь переполнена, сигнал отклонен")
                return False
        
        try:
            self.message_queue.put({
                'key': signal_key,
                'text': formatted_message
            }, block=False)
            logger.info(f"📤 Сигнал добавлен в очередь: {match.id} ~{analysis.next_signal.predicted_minute}' (счет {match.home_score}:{match.away_score})")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в очередь: {e}")
            return False

    def get_queue_size(self) -> int:
        return self.message_queue.qsize()
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы бота"""
        return {
            'queue_size': self.message_queue.qsize(),
            'sent_signals': len(self.sent_signals),
            'successful_sends': self.successful_sends,
            'failed_attempts': self.failed_attempts
        }
    
    def clear_old_signals(self, max_age_hours: int = 24):
        """Очищает старые сигналы из памяти"""
        with self.sent_lock:
            current_time = time.time()
            # Очищаем sent_signals_per_match (сигналы старше 24 часов)
            old_matches = [
                match_id for match_id, timestamp in self.sent_signals_per_match.items()
                if current_time - timestamp > max_age_hours * 3600
            ]
            for match_id in old_matches:
                del self.sent_signals_per_match[match_id]
            
            # Очищаем sent_signals (оставляем только последние 1000)
            if len(self.sent_signals) > 1000:
                self.sent_signals = set(list(self.sent_signals)[-1000:])
            
            logger.info(f"🧹 Очищено старых сигналов: {len(old_matches)} матчей")