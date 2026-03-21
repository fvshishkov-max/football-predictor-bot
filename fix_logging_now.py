# fix_logging_now.py
"""
Исправление логирования во всех файлах
"""

import os
import sys

def fix_file_logging(filename):
    """Добавляет правильное логирование в файл"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли настройка логирования
    if 'logging.basicConfig' not in content and 'logger = logging.getLogger' in content:
        # Добавляем настройку логирования в начало
        log_setup = '''
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
'''
        content = log_setup + content
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed logging in {filename}")

def create_test_log():
    """Создает тестовую запись в лог"""
    
    import logging
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=== LOGGING TEST ===")
    logger.info(f"Test log at {datetime.now().strftime('%H:%M:%S')}")
    
    print("✅ Test log created")

if __name__ == "__main__":
    from datetime import datetime
    
    # Создаем папку для логов
    os.makedirs('data/logs', exist_ok=True)
    
    # Исправляем основные файлы
    files_to_fix = ['run_fixed.py', 'app.py', 'predictor.py', 'telegram_bot_ultimate.py']
    
    for f in files_to_fix:
        if os.path.exists(f):
            fix_file_logging(f)
    
    # Создаем тестовый лог
    create_test_log()
    
    print("\n✅ Logging fixed!")
    print("Restart bot: python run_fixed.py")