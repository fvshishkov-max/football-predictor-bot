# run_fixed.py
#!/usr/bin/env python3
"""
Исправленная версия запуска с правильной обработкой потоков
"""
import sys
import os
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('football_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fix_windows_encoding():
    """Исправляет кодировку для Windows"""
    if sys.platform == "win32":
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
            sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
        else:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='backslashreplace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='backslashreplace')

def main():
    """Запуск приложения"""
    try:
        fix_windows_encoding()
        
        logger.info("🚀 Запуск AI Football Predictor...")
        
        # Импортируем после настройки
        from app import FootballApp
        
        # Создаем приложение
        app = FootballApp()
        
        # Запускаем в главном потоке
        app.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()