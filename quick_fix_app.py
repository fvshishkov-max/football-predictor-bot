# quick_fix_app.py
"""
Быстрое исправление app.py для отправки сигналов
"""

import re

def fix_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и исправляем блок отправки сигнала
    # Ищем строку с отправкой сигнала
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Если есть вызов send_message, оставляем
        if 'self.telegram_bot.send_message' in line:
            fixed_lines.append(line)
        # Если есть send_goal_signal, заменяем на send_message
        elif 'send_goal_signal' in line:
            fixed_lines.append(line.replace('send_goal_signal', 'send_message'))
        else:
            fixed_lines.append(line)
    
    new_content = '\n'.join(fixed_lines)
    
    # Добавляем логирование отправки
    new_content = new_content.replace(
        'self.telegram_bot.send_message(message)',
        'logger.info(f"Sending signal to Telegram")\n                    self.telegram_bot.send_message(message)'
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ app.py fixed")
    print("   - Replaced send_goal_signal with send_message")
    print("   - Added logging for sends")
    
    # Проверяем
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'send_message' in content:
        print("\n✅ send_message found in app.py")
    else:
        print("\n❌ send_message NOT found in app.py")

if __name__ == "__main__":
    fix_app()