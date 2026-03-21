
# Настройка логирования
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# telegram_bot_ultimate.py
"""
Максимально упрощенная версия с обходом SSL проблем
"""

import logging
import threading
import time
import socket
import http.client
import ssl
from queue import Queue

logger = logging.getLogger(__name__)

class TelegramBot:
    """Ультимативная версия с низкоуровневыми сокетами"""
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.message_queue = Queue()
        self.running = True
        self.max_retries = 5
        
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
                    
                    # Отправляем через низкоуровневый сокет
                    success = self._send_via_socket(chat_id, text)
                    
                    if success:
                        self.sent_count += 1
                        logger.info(f"✅ Отправлено #{self.sent_count} (очередь: {self.message_queue.qsize()})")
                    else:
                        self.failed_count += 1
                        logger.error(f"❌ Ошибка #{self.failed_count}")
                        time.sleep(10)
                        self.message_queue.put((chat_id, text))
                    
                    self.message_queue.task_done()
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике: {e}")
                time.sleep(5)
    
    def _send_via_socket(self, chat_id: str, text: str) -> bool:
        """Отправляет через низкоуровневый сокет в обход SSL проблем"""
        
        # Формируем простое текстовое сообщение без Markdown
        simple_text = self._simplify_text(text)
        
        # Формируем POST запрос вручную
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = f"--{boundary}\r\n"
        body += 'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        body += f"{chat_id}\r\n"
        body += f"--{boundary}\r\n"
        body += 'Content-Disposition: form-data; name="text"\r\n\r\n'
        body += f"{simple_text}\r\n"
        body += f"--{boundary}--\r\n"
        
        content_length = len(body.encode())
        
        request = (
            f"POST /bot{self.token}/sendMessage HTTP/1.1\r\n"
            f"Host: api.telegram.org\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        
        for attempt in range(self.max_retries):
            try:
                # Создаем сокет
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                
                # Подключаемся
                sock.connect(('api.telegram.org', 443))
                
                # Оборачиваем в SSL с минимальными требованиями
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = context.wrap_socket(sock, server_hostname='api.telegram.org')
                
                # Отправляем запрос
                ssl_sock.send(request.encode())
                
                # Получаем ответ
                response = ssl_sock.recv(4096).decode()
                
                ssl_sock.close()
                
                # Проверяем ответ
                if '200 OK' in response:
                    logger.debug(f"✅ Сокет: сообщение отправлено")
                    return True
                else:
                    logger.debug(f"❌ Сокет: ошибка в ответе")
                    
            except Exception as e:
                logger.debug(f"❌ Сокет ошибка (попытка {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(2)
        
        return False
    
    def _simplify_text(self, text: str) -> str:
        """Упрощает текст - убирает все спецсимволы"""
        # Убираем все Markdown символы
        import re
        text = re.sub(r'[*_`\[\]()#+\-=\{\}.!>]', '', text)
        
        # Заменяем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Обрезаем слишком длинные сообщения
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        return text
    
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