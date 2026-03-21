# add_keep_alive.py
"""
Добавляет keep-alive механизм в app.py
"""

def add_keep_alive():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем watchdog в _fast_loop
    watchdog_code = '''
        # Watchdog - проверяем, что бот не заснул
        if self.stats['api_calls'] > 0 and self.stats['api_calls'] % 10 == 0:
            logger.info(f"💪 Бот работает: {self.stats['api_calls']} циклов, {self.stats['signals_sent']} сигналов")
            self.stats['last_alive'] = datetime.now().isoformat()
            self.save_stats()'''
    
    # Находим место для вставки
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'self.stats["api_calls"] += 1' in line:
            lines.insert(i+2, watchdog_code)
            break
    
    content = '\n'.join(lines)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Keep-alive добавлен в app.py")

def fix_loop_interval():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Уменьшаем интервал проверки
    content = content.replace(
        'self.check_interval = 60',
        'self.check_interval = 30'
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Интервал проверки уменьшен до 30 секунд")

if __name__ == "__main__":
    add_keep_alive()
    fix_loop_interval()
    print("\nПерезапустите бота: python run_fixed.py")