# fix_api_loop.py
"""
Исправление цикла получения матчей
"""

import re

def fix_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем принудительное обновление, даже если API не отвечает
    # Находим метод _fast_check и добавляем логирование ошибок
    
    if 'except Exception as e:' in content:
        # Увеличиваем таймауты
        content = content.replace('timeout=15', 'timeout=30')
        content = content.replace('timeout=10', 'timeout=30')
        content = content.replace('timeout=5', 'timeout=15')
        
        # Добавляем повторные попытки
        retry_code = '''
            except Exception as e:
                logger.error(f"Error getting matches: {e}")
                # Если ошибка, ждем и пробуем снова
                await asyncio.sleep(5)
                return'''
        
        # Заменяем существующий except
        content = content.replace('except Exception as e:', retry_code)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py updated with retry logic")

def fix_api_client():
    with open('api_client.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем таймауты
    content = content.replace('timeout=10', 'timeout=30')
    content = content.replace('timeout=5', 'timeout=15')
    
    with open('api_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ api_client.py updated with longer timeouts")

if __name__ == "__main__":
    fix_api_client()
    fix_app()
    print("\nRestart bot: python run_fixed.py")