# force_check.py
"""
Принудительная проверка матчей вручную
Запустите: python force_check.py
"""

import asyncio
import logging
from datetime import datetime
from app import FastFootballApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_check():
    """Принудительно проверяет матчи"""
    app = FastFootballApp()
    
    logger.info("="*60)
    logger.info("🔍 ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА МАТЧЕЙ")
    logger.info("="*60)
    
    # Проверяем матчи
    await app._fast_check()
    
    logger.info("✅ Проверка завершена")
    
    # Закрываем соединения
    await app.api_client.close()

if __name__ == "__main__":
    asyncio.run(force_check())