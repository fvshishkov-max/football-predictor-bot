# telegram_bot_direct.py
"""
Telegram бот с прямой отправкой без очереди
"""

import logging
import requests
import time

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        logger.info(f"🚀 Bot initialized for channel {channel_id}")
    
    def send_message(self, text: str):
        """Отправляет сообщение напрямую без очереди"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                data={
                    'chat_id': self.channel_id,
                    'text': text
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully")
                return True
            else:
                logger.error(f"❌ Failed to send: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending: {e}")
            return False
    
    def send_goal_signal(self, match, analysis, custom_message):
        return self.send_message(custom_message)
    
    def stop(self):
        pass