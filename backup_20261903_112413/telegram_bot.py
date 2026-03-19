# telegram_bot.py
import logging
import threading
from datetime import datetime
from typing import Optional
from queue import Queue
import time
import requests

from models import Match, MatchAnalysis

logger = logging.getLogger(__name__)

class TelegramBot:
    """Максимально простой класс для отправки сообщений"""
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.message_queue = Queue()
        self.running = True
        self.max_retries = 5
        self.retry_delay = 2
        
        # Статистика
        self.sent_count = 0
        self.failed_count = 0
        
        # Запускаем обработчик
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info(f"🚀 Запущен обработчик для канала {channel_id}")
    
    def _process_queue(self):
        """Обрабатывает очередь сообщений"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    chat_id, text = self.message_queue.get(timeout=1)
                    
                    # Отправляем простой текст без какого-либо форматирования
                    success = self._send_plain_text(chat_id, text)
                    
                    if success:
                        self.sent_count += 1
                        logger.info(f"✅ Отправлено #{self.sent_count} (очередь: {self.message_queue.qsize()})")
                    else:
                        self.failed_count += 1
                        logger.error(f"❌ Ошибка #{self.failed_count}")
                        # Возвращаем в очередь
                        time.sleep(5)
                        self.message_queue.put((chat_id, text))
                    
                    self.message_queue.task_done()
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике: {e}")
                time.sleep(1)
    
    def _send_plain_text(self, chat_id: str, text: str) -> bool:
        """Отправляет простой текст без параметров"""
        for attempt in range(self.max_retries):
            try:
                # Максимально простой запрос
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    data={
                        'chat_id': chat_id,
                        'text': text
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:
                    # Rate limit - ждем
                    time.sleep(10)
                else:
                    logger.error(f"❌ Ошибка {response.status_code}: {response.text[:100]}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        return False
    
    def send_goal_signal(self, match: Match, analysis: Optional[MatchAnalysis] = None, custom_message: Optional[str] = None):
        """Добавляет сигнал в очередь"""
        try:
            if custom_message:
                # Убираем все возможные спецсимволы
                message_text = custom_message.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
            else:
                # Максимально простой формат
                home = match.home_team.name if match.home_team else "Home"
                away = match.away_team.name if match.away_team else "Away"
                message_text = f"⚽ {home} - {away} | {match.home_score}:{match.away_score} | {match.minute}'"
            
            self.message_queue.put((self.channel_id, message_text))
            logger.info(f"📨 Сигнал добавлен (очередь: {self.message_queue.qsize()})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False
    
    def send_message_to_channel(self, text: str):
        """Отправляет сообщение в канал"""
        clean_text = text.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
        self.message_queue.put((self.channel_id, clean_text))
        logger.info(f"📨 Сообщение добавлено в очередь")
    
    def get_stats(self):
        """Возвращает статистику"""
        return {
            'sent': self.sent_count,
            'failed': self.failed_count,
            'queue': self.message_queue.qsize()
        }
    
    def stop(self):
        """Останавливает обработчик"""
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info(f"⏹ Остановлен. Отправлено: {self.sent_count}, Ошибок: {self.failed_count}, В очереди: {self.message_queue.qsize()}")