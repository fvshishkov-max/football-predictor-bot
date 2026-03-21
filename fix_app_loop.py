# fix_app_loop.py
"""
Добавляет отладку в цикл app.py
"""

import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем логирование в _fast_check
if 'logger.debug("📡 Запрос live матчей...")' not in content:
    print("Adding debug logging to _fast_check...")
    
    # Находим начало метода _fast_check
    pattern = r'async def _fast_check\(self\):'
    match = re.search(pattern, content)
    
    if match:
        # Добавляем логирование
        new_content = content.replace(
            match.group(0),
            '''async def _fast_check(self):
        """Быстрая асинхронная проверка матчей"""
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Starting match check...")
            
            # Получаем матчи
            logger.debug("📡 Запрос live матчей...")
            matches = await self.api_client.get_live_matches()'''
        )
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Added debug logging")
    else:
        print("Method not found")

print("\nRestart bot to see debug logs")