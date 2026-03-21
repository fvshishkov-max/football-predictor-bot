# app_simple.py
"""
Простая версия app.py для тестирования
"""

import asyncio
import logging
import time
from datetime import datetime

import config
from api_client import UnifiedFastClient
from predictor import Predictor
from telegram_bot_direct import TelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleApp:
    def __init__(self):
        self.api_client = UnifiedFastClient()
        self.predictor = Predictor()
        self.telegram_bot = TelegramBot(config.TELEGRAM_TOKEN, config.CHANNEL_ID)
        self.running = True
        
    async def run_once(self):
        """Однократная проверка"""
        logger.info("Checking live matches...")
        matches = await self.api_client.get_live_matches()
        logger.info(f"Found {len(matches)} matches")
        
        signals_sent = 0
        for match in matches:
            signal = self.predictor.analyze_live_match(match)
            if signal:
                message = signal.get('message')
                if message:
                    self.telegram_bot.send_message(message)
                    signals_sent += 1
                    logger.info(f"Sent signal for {match.home_team.name} vs {match.away_team.name}")
                    await asyncio.sleep(1)  # Пауза между отправками
        
        logger.info(f"Total signals sent: {signals_sent}")
    
    async def run_loop(self):
        """Бесконечный цикл"""
        logger.info("Starting simple app loop...")
        while self.running:
            try:
                await self.run_once()
                logger.info(f"Waiting 60 seconds...")
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        self.running = False

async def main():
    app = SimpleApp()
    try:
        await app.run_loop()
    except KeyboardInterrupt:
        app.stop()
        await app.api_client.close()
        logger.info("Stopped")

if __name__ == "__main__":
    asyncio.run(main())