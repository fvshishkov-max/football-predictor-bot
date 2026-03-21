# setup_logging.py
"""
Настройка логирования для бота
Запуск: python setup_logging.py
"""

import os
import logging
import sys

def setup_logging():
    """Настраивает логирование в файл и консоль"""
    
    # Создаем папку для логов
    os.makedirs('data/logs', exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print("✅ Логирование настроено")
    print(f"   Лог-файл: data/logs/app.log")
    
    # Проверяем запись
    logger = logging.getLogger(__name__)
    logger.info("Логирование запущено")
    
    return logger

if __name__ == "__main__":
    setup_logging()