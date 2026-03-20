# telegram_bot_simple.py
"""
Максимально упрощенная версия Telegram бота
"""

import logging
import threading
import time
import requests
from queue import Queue

logger = logging.getLogger(__name__)

class TelegramBot:
    """Максимально простой класс для отправки сообщений"""
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.message_queue = Queue()
        self.running = True
        self.max_retries = 10
        self.retry_delay = 5
        
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
                    
                    # Упрощаем текст - убираем все спецсимволы
                    simple_text = self._simplify_text(text)
                    
                    # Пробуем отправить
                    success = self._send_simple(chat_id, simple_text)
                    
                    if success:
                        self.sent_count += 1
                        logger.info(f"✅ Отправлено #{self.sent_count} (очередь: {self.message_queue.qsize()})")
                    else:
                        self.failed_count += 1
                        logger.error(f"❌ Ошибка #{self.failed_count}")
                        # Возвращаем в очередь
                        time.sleep(10)
                        self.message_queue.put((chat_id, text))
                    
                    self.message_queue.task_done()
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике: {e}")
                time.sleep(5)
    
    def _simplify_text(self, text: str) -> str:
        """Упрощает текст - убирает все спецсимволы"""
        # Заменяем эмодзи на текстовые аналоги
        replacements = {
            '🔴': '[RED]',
            '🟠': '[ORANGE]',
            '🟡': '[YELLOW]',
            '🟢': '[GREEN]',
            '⚪': '[WHITE]',
            '⚽': '[BALL]',
            '🏟': '[STADIUM]',
            '📊': '[STATS]',
            '📈': '[CHART]',
            '🎯': '[TARGET]',
            '⏱': '[TIME]',
            '✅': '[YES]',
            '❌': '[NO]',
            '━━━━━━━━━━━━━━━━━━━━━': '-------------------',
        }
        
        for emoji, text_replacement in replacements.items():
            text = text.replace(emoji, text_replacement)
        
        # Убираем все остальные спецсимволы
        import re
        text = re.sub(r'[*_`\[\]()#+\-=\{\}.!>]', '', text)
        
        return text
    
    def _send_simple(self, chat_id: str, text: str) -> bool:
        """Отправляет простой текст"""
        for attempt in range(self.max_retries):
            try:
                # Максимально простой запрос
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    data={
                        'chat_id': chat_id,
                        'text': text
                    },
                    timeout=30,
                    verify=True  # Проверка SSL
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"❌ Ошибка {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.SSLError as e:
                logger.error(f"🔒 SSL ошибка (попытка {attempt + 1}): {e}")
                # Пробуем без проверки SSL
                try:
                    response = requests.post(
                        f"{self.api_url}/sendMessage",
                        data={
                            'chat_id': chat_id,
                            'text': text
                        },
                        timeout=30,
                        verify=False  # Без проверки SSL
                    )
                    if response.status_code == 200:
                        return True
                except:
                    pass
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Таймаут (попытка {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Ошибка соединения (попытка {attempt + 1})")
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return False
    
    def send_message(self, text: str):
        """Отправляет сообщение в канал"""
        self.message_queue.put((self.channel_id, text))
        logger.info(f"📨 Сообщение добавлено в очередь (очередь: {self.message_queue.qsize()})")
    
    def stop(self):
        """Останавливает обработчик"""
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info(f"⏹ Остановлен. Отправлено: {self.sent_count}, Ошибок: {self.failed_count}")