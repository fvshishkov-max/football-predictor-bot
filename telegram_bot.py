# telegram_bot.py
import asyncio
import logging
from telegram import Bot
from telegram.error import TimedOut, RetryAfter
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
        self.max_retries = 3
        self.retry_delay = 2
        self.message_queue = Queue(maxsize=50)
        self.last_send_time = 0
        self.min_interval = 4
        self.sent_lock = threading.Lock()
        self.start_queue_processor()
        logger.info(f"🚀 Запущен обработчик очереди Telegram для канала {channel_id}")

    def start_queue_processor(self):
        def process_queue():
            logger.info("🚀 Запущен обработчик очереди Telegram")
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
                    
                    current_time = time.time()
                    time_since_last = current_time - self.last_send_time
                    if time_since_last < self.min_interval:
                        wait_time = self.min_interval - time_since_last
                        logger.debug(f"Ожидание {wait_time:.1f} сек")
                        time.sleep(wait_time)
                    
                    success = self._send_message_sync(message_data['text'])
                    if success:
                        with self.sent_lock:
                            self.sent_signals.add(message_data['key'])
                            logger.info(f"✅ Сигнал отправлен: {message_data['key']}")
                        self.last_send_time = time.time()
                    else:
                        logger.error(f"❌ Не удалось отправить {message_data['key']}")
                    
                    self.message_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"Ошибка в обработчике очереди: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=process_queue, name="TelegramQueue", daemon=True)
        thread.start()

    def _send_message_sync(self, text: str) -> bool:
        """Отправляет сообщение синхронно (без Markdown)"""
        for attempt in range(self.max_retries):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                bot = Bot(token=self.token)
                
                # Отправляем без parse_mode (обычный текст)
                loop.run_until_complete(
                    asyncio.wait_for(
                        bot.send_message(
                            chat_id=self.channel_id,
                            text=text
                        ),
                        timeout=15.0
                    )
                )
                loop.close()
                return True
                
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1}/{self.max_retries} не удалась: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                if 'loop' in locals() and loop.is_running():
                    loop.close()
        
        return False

    def send_goal_signal(self, match: Match, analysis: MatchAnalysis, formatted_message: str) -> bool:
        """Отправляет сигнал о голе"""
        if not analysis.next_signal:
            return False
        
        signal_key = f"{match.id}_{analysis.next_signal.predicted_minute}"
        
        with self.sent_lock:
            if signal_key in self.sent_signals:
                return True
        
        if self.message_queue.qsize() >= 50:
            logger.warning("⚠️ Очередь переполнена")
            return False
        
        try:
            self.message_queue.put({
                'key': signal_key,
                'text': formatted_message
            }, block=False)
            logger.info(f"📤 Сигнал в очередь: {match.id} ~{analysis.next_signal.predicted_minute}'")
            return True
        except:
            return False

    def get_queue_size(self) -> int:
        return self.message_queue.qsize()