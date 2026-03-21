# telegram_bot_fixed.py
"""
Исправленная версия Telegram бота с гарантированной отправкой
"""

import logging
import threading
import time
import requests
from queue import Queue

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.message_queue = Queue()
        self.running = True
        self.sent_count = 0
        self.failed_count = 0
        
        # Запускаем обработчик
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info(f"🚀 Bot started for channel {channel_id}")
    
    def _process_queue(self):
        """Обрабатывает очередь сообщений"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    chat_id, text = self.message_queue.get(timeout=1)
                    
                    # Отправляем с повторными попытками
                    success = self._send_message(chat_id, text)
                    
                    if success:
                        self.sent_count += 1
                        logger.info(f"✅ Sent #{self.sent_count} (queue: {self.message_queue.qsize()})")
                    else:
                        self.failed_count += 1
                        logger.error(f"❌ Failed #{self.failed_count}")
                        # Возвращаем в очередь
                        time.sleep(2)
                        self.message_queue.put((chat_id, text))
                    
                    self.message_queue.task_done()
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Queue error: {e}")
                time.sleep(1)
    
    def _send_message(self, chat_id: str, text: str) -> bool:
        """Отправляет сообщение с повторными попытками"""
        for attempt in range(3):
            try:
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    data={
                        'chat_id': chat_id,
                        'text': text
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.debug(f"Attempt {attempt+1} failed: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"Attempt {attempt+1} error: {e}")
            
            if attempt < 2:
                time.sleep(1)
        
        return False
    
    def send_message(self, text: str):
        """Добавляет сообщение в очередь"""
        self.message_queue.put((self.channel_id, text))
        logger.info(f"📨 Message added (queue: {self.message_queue.qsize()})")
        return True
    
    def send_goal_signal(self, match, analysis, custom_message):
        """Алиас для send_message"""
        return self.send_message(custom_message)
    
    def stop(self):
        """Останавливает обработчик и ждет отправки всех сообщений"""
        self.running = False
        
        # Ждем, пока очередь не опустеет (макс 10 секунд)
        wait_time = 0
        while not self.message_queue.empty() and wait_time < 10:
            time.sleep(0.5)
            wait_time += 0.5
        
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        logger.info(f"⏹ Stopped. Sent: {self.sent_count}, Failed: {self.failed_count}, Queue left: {self.message_queue.qsize()}")