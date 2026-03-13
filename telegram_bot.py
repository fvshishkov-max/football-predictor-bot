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

COUNTRY_FLAGS = {
    'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'eng': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'spain': '🇪🇸', 'esp': '🇪🇸',
    'italy': '🇮🇹', 'ita': '🇮🇹',
    'germany': '🇩🇪', 'ger': '🇩🇪',
    'france': '🇫🇷', 'fra': '🇫🇷',
    'netherlands': '🇳🇱', 'ned': '🇳🇱',
    'portugal': '🇵🇹', 'por': '🇵🇹',
    'turkey': '🇹🇷', 'tur': '🇹🇷',
    'russia': '🇷🇺', 'rus': '🇷🇺',
    'ukraine': '🇺🇦', 'ukr': '🇺🇦',
    'belgium': '🇧🇪', 'bel': '🇧🇪',
    'switzerland': '🇨🇭', 'sui': '🇨🇭',
    'austria': '🇦🇹', 'aut': '🇦🇹',
    'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'sco': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
    'wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'wal': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
    'usa': '🇺🇸', 'brazil': '🇧🇷', 'bra': '🇧🇷',
    'argentina': '🇦🇷', 'arg': '🇦🇷', 'japan': '🇯🇵', 'jpn': '🇯🇵',
}

class TelegramBot:
    """Класс для работы с Telegram ботом с очередью сообщений"""
    
    def __init__(self, token: str, channel_id: str = "-1001679913676"):
        self.token = token
        self.channel_id = channel_id
        self.sent_signals = set()
        self.max_retries = 3
        self.retry_delay = 2
        
        # Очередь сообщений
        self.message_queue = Queue(maxsize=50)
        self.last_send_time = 0
        self.min_interval = 4  # Увеличим интервал до 4 секунд
        
        # Блокировка
        self.sent_lock = threading.Lock()
        
        # Запускаем обработчик очереди
        self.start_queue_processor()
    
    def start_queue_processor(self):
        """Запускает фоновый поток для обработки очереди"""
        def process_queue():
            logger.info("🚀 Запущен обработчик очереди Telegram")
            while True:
                try:
                    # Получаем сообщение из очереди
                    message_data = self.message_queue.get()
                    if message_data is None:
                        break
                    
                    # Проверяем, не отправляли ли уже
                    with self.sent_lock:
                        if message_data['key'] in self.sent_signals:
                            logger.debug(f"⏭️ Сигнал {message_data['key']} уже отправлен")
                            self.message_queue.task_done()
                            continue
                    
                    # Ждем необходимый интервал
                    current_time = time.time()
                    time_since_last = current_time - self.last_send_time
                    if time_since_last < self.min_interval:
                        wait_time = self.min_interval - time_since_last
                        logger.debug(f"Ожидание {wait_time:.1f} сек")
                        time.sleep(wait_time)
                    
                    # Отправляем сообщение
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
        """Синхронная отправка сообщения"""
        for attempt in range(self.max_retries):
            try:
                # Создаем новый event loop для каждой попытки
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Создаем нового клиента
                bot = Bot(token=self.token)
                
                # Отправляем
                loop.run_until_complete(
                    asyncio.wait_for(
                        bot.send_message(
                            chat_id=self.channel_id,
                            text=text,
                            parse_mode='Markdown'
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
    
    def _get_country_flag(self, country_code: str) -> str:
        """Возвращает флаг страны по коду"""
        if not country_code:
            return "🌍"
        country_code = country_code.lower().strip()
        return COUNTRY_FLAGS.get(country_code, "🌍")
    
    def _format_match_header(self, match: Match) -> str:
        """Форматирует заголовок матча с флагами"""
        home_flag = self._get_country_flag(match.home_team.country_code)
        away_flag = self._get_country_flag(match.away_team.country_code)
        return f"{home_flag} **{match.home_team.name}** vs {away_flag} **{match.away_team.name}**"
    
    def send_goal_signal(self, match: Match, analysis: MatchAnalysis, formatted_message: str) -> bool:
        """Отправляет сигнал на гол в Telegram через очередь"""
        if not analysis.next_signal:
            return False
        
        signal_key = f"{match.id}_{analysis.next_signal.predicted_minute}"
        
        # Проверяем в очереди
        with self.sent_lock:
            if signal_key in self.sent_signals:
                return True
        
        # Проверяем размер очереди
        if self.message_queue.qsize() >= 50:
            logger.warning("⚠️ Очередь переполнена")
            return False
        
        # Добавляем в очередь
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
        """Возвращает размер очереди"""
        return self.message_queue.qsize()