# optimize_requests.py
"""
Оптимизация частоты запросов к API
"""

import re

def optimize_api_client():
    """Уменьшает частоту запросов в api_client.py"""
    
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем интервал rate limit
    # Ищем места с паузой 0.5с и увеличиваем
    content = content.replace('time.sleep(0.5)', 'time.sleep(1.0)')
    content = content.replace('await asyncio.sleep(0.5)', 'await asyncio.sleep(1.0)')
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Rate limit паузы увеличены до 1 секунды")

def add_batch_processing():
    """Добавляет пакетную обработку матчей"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем задержку между матчами
    if 'await asyncio.sleep(0.5)' not in content:
        # Находим цикл обработки матчей
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'for match in filtered:' in line:
                # Добавляем задержку после обработки
                lines.insert(i+50, '                    await asyncio.sleep(0.2)')
                break
        
        content = '\n'.join(lines)
        print("✅ Добавлена задержка между матчами")
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    optimize_api_client()
    add_batch_processing()
    print("\nRestart bot: python run_fixed.py")