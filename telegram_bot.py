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
        self.sent_signals = set()
        self.max_retries = 5  # Увеличили количество попыток
        self.retry_delay = 3   # Увеличили задержку
        self.message_queue = Queue(maxsize=100)  # Увеличили размер очереди
        self.last_send_time = 0
        self.min_interval = 5   # Увеличили интервал между сообщениями
        self.sent_lock = threading.Lock()
        self.failed_attempts = 0
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
                        if message_data['key'] in self.sent_signals:
                            logger.debug(f"⏭️ Сигнал {message_data['key']} уже отправлен")
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
                            logger.info(f"✅ Сигнал отправлен: {message_data['key']}")
                        self.last_send_time = time.time()
                        consecutive_failures = 0
                        self.failed_attempts = 0
                    else:
                        consecutive_failures += 1
                        self.failed_attempts += 1
                        logger.error(f"❌ Не удалось отправить {message_data['key']} (попыток: {consecutive_failures})")
                        
                        # Если много ошибок подряд, увеличиваем интервал
                        if consecutive_failures > 3:
                            logger.warning(f"⚠️ Много ошибок подряд, увеличиваем интервал до 10с")
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
                loop.run_until_complete(
                    asyncio.wait_for(
                        bot.send_message(
                            chat_id=self.channel_id,
                            text=text
                        ),
                        timeout=20.0  # Увеличили таймаут
                    )
                )
                loop.close()
                return True
                
            except TimedOut:
                logger.warning(f"⏰ Таймаут {attempt + 1}/{self.max_retries}, повтор через {self.retry_delay * (attempt + 1)}с")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            except NetworkError as e:
                logger.warning(f"🌐 Сетевая ошибка {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 2))
                    
            except Exception as e:
                logger.warning(f"❌ Ошибка {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            finally:
                try:
                    if 'loop' in locals() and loop.is_running():
                        loop.close()
                except:
                    pass
        
        return False

    def send_goal_signal(self, match: Match, analysis: MatchAnalysis, formatted_message: str) -> bool:
        """Отправляет сигнал о голе"""
        if not analysis.next_signal:
            return False
        
        signal_key = f"{match.id}_{analysis.next_signal.predicted_minute}"
        
        with self.sent_lock:
            if signal_key in self.sent_signals:
                logger.debug(f"⏭️ Сигнал {signal_key} уже был отправлен")
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
            'failed_attempts': self.failed_attempts
        }