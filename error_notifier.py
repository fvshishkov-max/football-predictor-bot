# error_notifier.py
import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class ErrorNotifier:
    """Система уведомлений об ошибках в Telegram"""
    
    ddef __init__(self, telegram_bot, channel_id: str, admin_id: Optional[str] = None):
        self.telegram_bot = telegram_bot
        self.channel_id = channel_id  # используется переданный ID
        self.admin_id = admin_id or channel_id
        self.error_counts = defaultdict(int)
        self.last_notification = defaultdict(lambda: datetime.min)
        self.cooldown_period = timedelta(minutes=5)  # Не чаще раза в 5 минут
        self.max_errors_before_alert = 3  # 3 одинаковые ошибки подряд
        
    def notify_error(self, error_type: str, error_msg: str, 
                     tb: Optional[str] = None, context: Optional[Dict] = None):
        """Отправляет уведомление об ошибке"""
        self.error_counts[error_type] += 1
        now = datetime.now()
        
        # Проверяем, нужно ли уведомлять
        if now - self.last_notification[error_type] < self.cooldown_period:
            if self.error_counts[error_type] < self.max_errors_before_alert:
                logger.debug(f"Ошибка {error_type} подавлена (cooldown)")
                return
        
        # Формируем сообщение
        if self.error_counts[error_type] >= self.max_errors_before_alert:
            severity = "🔴 **КРИТИЧЕСКАЯ ОШИБКА**"
        else:
            severity = "🟡 **ОШИБКА**"
        
        message = f"{severity}\n\n"
        message += f"**Тип:** {error_type}\n"
        message += f"**Время:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"**Сообщение:** {error_msg}\n"
        message += f"**Частота:** {self.error_counts[error_type]} раз\n"
        
        if context:
            message += f"\n**Контекст:**\n"
            for key, value in context.items():
                message += f"  • {key}: {value}\n"
        
        if tb and self.error_counts[error_type] >= self.max_errors_before_alert:
            # Для критических ошибок добавляем traceback
            short_tb = tb.split('\n')[-5:]  # Последние 5 строк
            message += f"\n**Traceback:**\n```\n" + '\n'.join(short_tb) + "\n```"
        
        # Отправляем в Telegram
        try:
            self.telegram_bot.message_queue.put({
                'key': f"error_{now.timestamp()}",
                'text': message
            })
            logger.info(f"✅ Уведомление об ошибке отправлено: {error_type}")
            self.last_notification[error_type] = now
            
            # Если ошибка критическая, сбрасываем счетчик
            if self.error_counts[error_type] >= self.max_errors_before_alert:
                self.error_counts[error_type] = 0
                
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def notify_api_failure(self, api_name: str, endpoint: str, status_code: int, response: str):
        """Уведомление о сбое API"""
        context = {
            'endpoint': endpoint,
            'status_code': status_code,
            'response': response[:200]  # Первые 200 символов
        }
        self.notify_error(
            error_type=f"API_{api_name}",
            error_msg=f"Сбой при запросе к {api_name}",
            context=context
        )
    
    def notify_rate_limit(self, api_name: str, remaining: int, reset_time: int):
        """Уведомление о достижении rate limit"""
        context = {
            'remaining': remaining,
            'reset_in': f"{reset_time}с"
        }
        self.notify_error(
            error_type=f"RATE_LIMIT_{api_name}",
            error_msg=f"Достигнут rate limit для {api_name}",
            context=context
        )
    
    def get_stats(self) -> Dict:
        """Возвращает статистику ошибок"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts)
        }