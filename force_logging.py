# force_logging.py
"""
Принудительное добавление логирования в ключевые файлы
"""

import re

def add_logging_to_file(filename, target_line):
    """Добавляет логирование в файл"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Проверяем, есть ли уже импорт
    has_import = any('import logging' in line for line in lines)
    
    if not has_import:
        lines.insert(1, 'import logging\n')
        print(f"  Added import to {filename}")
    
    # Проверяем, есть ли logger
    has_logger = any('logger = logging.getLogger' in line for line in lines)
    
    if not has_logger:
        for i, line in enumerate(lines):
            if target_line in line:
                lines.insert(i+1, '\nlogger = logging.getLogger(__name__)\n')
                print(f"  Added logger to {filename}")
                break
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    print("="*70)
    print("FORCE ADD LOGGING")
    print("="*70)
    
    files = [
        ('predictor.py', 'class Predictor:'),
        ('app.py', 'class FastFootballApp:'),
        ('api_client.py', 'class UnifiedFastClient:'),
        ('telegram_bot.py', 'class TelegramBot:')
    ]
    
    for file, target in files:
        print(f"\nProcessing {file}...")
        add_logging_to_file(file, target)
    
    print("\n" + "="*70)
    print("Done! Restart bot: python run_fixed.py")
    print("="*70)

if __name__ == "__main__":
    main()