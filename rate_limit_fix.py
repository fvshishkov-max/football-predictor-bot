# rate_limit_fix.py
"""
Увеличение интервалов между запросами для избежания rate limit
"""

import re

def fix_rate_limit():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем интервалы
    content = content.replace('time.sleep(0.5)', 'time.sleep(2.0)')
    content = content.replace('await asyncio.sleep(0.5)', 'await asyncio.sleep(2.0)')
    
    # Уменьшаем максимальное количество запросов в секунду
    content = content.replace('if len(self.request_times) >= 10:', 'if len(self.request_times) >= 5:')
    content = content.replace('if len(self.request_times) >= 20:', 'if len(self.request_times) >= 10:')
    
    # Добавляем дополнительную задержку при rate limit
    retry_code = '''
            if response.status_code == 429:
                logger.warning(f"Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return await self._make_request(endpoint, params, use_cache)'''
    
    content = content.replace('if response.status_code == 429:', retry_code)
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Rate limit fixes applied:")
    print("   - Sleep increased to 2.0s")
    print("   - Max requests per second: 5")
    print("   - 60s wait on 429 error")

if __name__ == "__main__":
    fix_rate_limit()