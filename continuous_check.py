# continuous_check.py
"""
Непрерывная проверка матчей (каждые 30 секунд)
Запустите: python continuous_check.py
"""

import asyncio
import logging
import time
from datetime import datetime
from app import FastFootballApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContinuousChecker:
    """Непрерывная проверка матчей"""
    
    def __init__(self):
        self.app = FastFootballApp()
        self.running = True
        self.check_count = 0
    
    async def check_loop(self):
        """Бесконечный цикл проверки"""
        logger.info("="*60)
        logger.info("🔄 ЗАПУСК НЕПРЕРЫВНОЙ ПРОВЕРКИ")
        logger.info("="*60)
        
        while self.running:
            self.check_count += 1
            logger.info(f"\n📊 ПРОВЕРКА #{self.check_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                await self.app._fast_check()
                logger.info(f"✅ Проверка #{self.check_count} завершена")
            except Exception as e:
                logger.error(f"❌ Ошибка в проверке #{self.check_count}: {e}")
            
            # Ждем 30 секунд до следующей проверки
            logger.info("💤 Ожидание 30 секунд...")
            await asyncio.sleep(30)
    
    def stop(self):
        """Останавливает проверку"""
        self.running = False
        logger.info("⏹ Проверка остановлена")

async def main():
    checker = ContinuousChecker()
    try:
        await checker.check_loop()
    except KeyboardInterrupt:
        checker.stop()
        await checker.app.api_client.close()
        logger.info("👋 Программа завершена")

if __name__ == "__main__":
    asyncio.run(main())