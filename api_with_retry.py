# api_with_retry.py
"""
Исправление API клиента с повторными попытками при rate limit
"""

import re

def fix_api_client():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем задержки
    content = content.replace('time.sleep(0.5)', 'time.sleep(2.0)')
    content = content.replace('await asyncio.sleep(0.5)', 'await asyncio.sleep(2.0)')
    
    # Добавляем обработку rate limit с длительной паузой
    rate_limit_handler = '''
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return await self._make_request(endpoint, params, use_cache)'''
    
    content = content.replace('if response.status_code == 429:', rate_limit_handler)
    
    # Уменьшаем количество параллельных запросов
    content = content.replace('if len(self.request_times) >= 10:', 'if len(self.request_times) >= 3:')
    content = content.replace('if len(self.request_times) >= 20:', 'if len(self.request_times) >= 5:')
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ API client fixed:")
    print("   - Sleep increased to 2.0s")
    print("   - Max requests per second: 3")
    print("   - 60s wait on 429 error")

if __name__ == "__main__":
    fix_api_client()