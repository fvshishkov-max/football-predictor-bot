# fix_logging.py
import logging
import sys

def setup_logging():
    """Настраивает логирование с принудительной записью в файл"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем файловый handler с принудительной записью
    file_handler = logging.FileHandler('football_bot.log', encoding='utf-8', mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Настраиваем консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Удаляем старые handlers
    root_logger.handlers.clear()
    
    # Добавляем новые handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Принудительно пишем тестовую запись
    logging.info("✅ Система логирования инициализирована")
    logging.info(f"📁 Лог-файл: football_bot.log")
    
    return root_logger

if __name__ == "__main__":
    logger = setup_logging()
    print("✅ Логирование настроено. Проверьте файл football_bot.log")