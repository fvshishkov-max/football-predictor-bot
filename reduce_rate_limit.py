# reduce_rate_limit.py
"""
Уменьшение частоты запросов к API
"""

import re

def fix_rate_limit():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем интервал между запросами
    content = content.replace('time.sleep(0.5)', 'time.sleep(1.5)')
    content = content.replace('await asyncio.sleep(0.5)', 'await asyncio.sleep(1.5)')
    
    # Увеличиваем лимит запросов в секунду
    content = content.replace('if len(self.request_times) >= 10:', 'if len(self.request_times) >= 5:')
    content = content.replace('if len(self.request_times) >= 20:', 'if len(self.request_times) >= 10:')
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Rate limit reduced:")
    print("   - Sleep increased to 1.5s")
    print("   - Max requests per second reduced")

if __name__ == "__main__":
    fix_rate_limit()