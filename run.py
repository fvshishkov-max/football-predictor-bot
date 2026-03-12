# run.py - замените секцию с logging на:

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настраиваем логирование ДО импорта других модулей
from fix_logging import setup_logging
logger = setup_logging()

# Теперь импортируем остальные модули
from app import FootballApp

def main():
    try:
        logger.info("🚀 Запуск AI Football Predictor...")
        app = FootballApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()