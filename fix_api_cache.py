# fix_api_cache.py
"""
Исправление проблемы с кэшированием API
"""

import re

def fix_api_client():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем паузу между запросами и отключаем кэш для live матчей
    # Находим метод get_live_matches и отключаем кэш
    new_get_live = '''    async def get_live_matches(self) -> List[Match]:
        params = {"Live": "true", "Limit": 100, "TimeZone": 3}
        # Отключаем кэш для live матчей - всегда свежие данные
        data = await self._make_request("/Games/list", params, use_cache=False)
        return self._parse_matches_list(data) if data else []'''
    
    # Заменяем
    content = content.replace(
        'params = {"Live": "true", "Limit": 100, "TimeZone": 3}\n        data = await self._make_request("/Games/list", params, use_cache=False)',
        'params = {"Live": "true", "Limit": 100, "TimeZone": 3}\n        # Отключаем кэш для live матчей - всегда свежие данные\n        data = await self._make_request("/Games/list", params, use_cache=False)'
    )
    
    # Увеличиваем таймауты и уменьшаем rate limit
    content = content.replace('await asyncio.sleep(5)', 'await asyncio.sleep(2)')
    content = content.replace('waiting 5 seconds', 'waiting 2 seconds')
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ api_client.py исправлен")
    print("   • Отключен кэш для live матчей")
    print("   • Уменьшена задержка rate limit до 2 секунд")

def fix_app_retry():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем принудительную повторную попытку при пустых матчах
    retry_code = '''
            if not matches:
                logger.warning(f"📭 Нет live матчей, повторная попытка через 5 секунд")
                await asyncio.sleep(5)
                # Принудительно очищаем кэш API
                if hasattr(self.api_client, 'sstats'):
                    self.api_client.sstats.cache = {}
                return'''
    
    # Заменяем старый блок
    content = content.replace(
        'if not matches:\n                logger.debug("📭 Нет live матчей")\n                return',
        retry_code
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py исправлен")
    print("   • Добавлена повторная попытка при пустых матчах")
    print("   • Принудительная очистка кэша")

def add_force_refresh():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем принудительное обновление каждые 3 цикла
    force_refresh = '''
        # Принудительное обновление каждые 3 цикла
        if self.stats['api_calls'] % 3 == 0 and self.stats['api_calls'] > 0:
            logger.info("🔄 Принудительная очистка кэша API")
            if hasattr(self.api_client, 'sstats'):
                self.api_client.sstats.cache = {}'''
    
    # Находим место после проверки матчей
    content = content.replace(
        'if not matches:',
        force_refresh + '\n            if not matches:'
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Добавлено принудительное обновление кэша каждые 3 цикла")

if __name__ == "__main__":
    fix_api_client()
    fix_app_retry()
    add_force_refresh()
    print("\n" + "="*60)
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("="*60)
    print("\nПерезапустите бота: python run_fixed.py")