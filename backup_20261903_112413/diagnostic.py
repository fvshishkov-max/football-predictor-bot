# diagnostic.py
import os
import sys
import json
from datetime import datetime

def check_files():
    """Проверяет наличие всех необходимых файлов"""
    print("\n🔍 ПРОВЕРКА ФАЙЛОВ:")
    print("-"*40)
    
    required_files = [
        'app.py',
        'predictor.py',
        'telegram_bot.py',
        'api_client.py',
        'models.py',
        'ui.py',
        'config.py',
        'bot_state.py',
        'run.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} - {size} байт")
        else:
            print(f"❌ {file} - ОТСУТСТВУЕТ")
    
    print("\n📁 ПРОВЕРКА ФАЙЛОВ ДАННЫХ:")
    data_files = ['signal_accuracy.json', 'bot_stats.json', 'football_bot.log']
    data_files.extend([f for f in os.listdir('.') if f.startswith('signals_history_')])
    
    for file in data_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"📄 {file} - {size} байт (изменен: {mod_time})")

def check_imports():
    """Проверяет возможность импорта модулей"""
    print("\n🔍 ПРОВЕРКА ИМПОРТОВ:")
    print("-"*40)
    
    modules = [
        ('tkinter', 'GUI библиотека'),
        ('asyncio', 'Асинхронность'),
        ('aiohttp', 'HTTP клиент'),
        ('telegram', 'Telegram API'),
        ('numpy', 'Научные вычисления'),
        ('scipy', 'Статистика'),
        ('sklearn', 'Машинное обучение')
    ]
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError as e:
            print(f"❌ {module} - {description} (ОШИБКА: {e})")

def check_config():
    """Проверяет конфигурацию"""
    print("\n🔍 ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("-"*40)
    
    try:
        import config
        print(f"✅ BOT_TOKEN: {config.BOT_TOKEN[:5]}...{config.BOT_TOKEN[-5:]}")
        print(f"✅ CHANNEL_ID: {config.CHANNEL_ID}")
        print(f"✅ SSTATS_API_KEY: {config.SSTATS_API_KEY[:5]}...")
        print(f"✅ USE_MOCK_DATA: {config.USE_MOCK_DATA}")
        print(f"✅ UPDATE_INTERVAL: {config.UPDATE_INTERVAL} сек")
    except Exception as e:
        print(f"❌ Ошибка загрузки config: {e}")

def test_api_connection():
    """Тестирует подключение к API"""
    print("\n🔍 ТЕСТ API СОЕДИНЕНИЯ:")
    print("-"*40)
    
    try:
        import asyncio
        from api_client import SStatsClient
        import config
        
        async def test():
            client = SStatsClient(config.SSTATS_API_KEY, use_mock=False)
            matches = await client.get_live_matches()
            print(f"✅ API доступно, найдено матчей: {len(matches)}")
            if matches:
                print(f"   Пример: {matches[0].home_team.name} vs {matches[0].away_team.name}")
        
        asyncio.run(test())
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")

def main():
    """Главная функция диагностики"""
    print("\n" + "="*60)
    print("🔧 ДИАГНОСТИКА СИСТЕМЫ FOOTBALL PREDICTOR")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python версия: {sys.version}")
    print(f"Платформа: {sys.platform}")
    
    check_files()
    check_imports()
    check_config()
    test_api_connection()
    
    print("\n" + "="*60)
    print("✅ Диагностика завершена")
    print("="*60)

if __name__ == "__main__":
    main()