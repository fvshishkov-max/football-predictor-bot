# fix_telegram_method.py
"""
Добавляет недостающий метод send_message в telegram_bot_ultimate.py
"""

import re

with open('telegram_bot_ultimate.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем, есть ли метод send_message
if 'def send_message' not in content:
    print("Adding send_message method...")
    
    # Добавляем метод после send_message_to_channel
    new_method = '''
    def send_message(self, text: str):
        """Отправляет сообщение в канал"""
        self.message_queue.put((self.channel_id, text))
        logger.info(f"📨 Сообщение добавлено в очередь (очередь: {self.message_queue.qsize()})")
        return True
'''
    
    # Находим место для вставки (после send_goal_signal или в конце)
    if 'def send_goal_signal' in content:
        content = content.replace('def send_goal_signal', new_method + '\n    def send_goal_signal')
    else:
        content += new_method
    
    with open('telegram_bot_ultimate.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ send_message method added")
else:
    print("✅ send_message method already exists")

print("\nRestart bot: python run_fixed.py")