#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Точка входа в приложение
"""

import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Основная функция"""
    try:
        logger.info("🚀 Запуск AI Football Predictor...")
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from app import FootballApp
        
        # Создаем и запускаем приложение
        app = FootballApp()
        app.start_monitoring()
        
        logger.info("✅ Приложение запущено")
        
        # Держим основной поток активным
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 Получен сигнал завершения")
            app.stop_monitoring()
            logger.info("👋 Приложение остановлено")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()