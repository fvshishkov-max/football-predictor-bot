# fix_telegram.py
"""
Замена telegram_bot_ultimate.py на исправленную версию
"""

import shutil
import os

# Создаем резервную копию
if os.path.exists('telegram_bot_ultimate.py'):
    shutil.copy('telegram_bot_ultimate.py', 'telegram_bot_ultimate_backup.py')
    print("✅ Backup created: telegram_bot_ultimate_backup.py")

# Копируем исправленную версию
shutil.copy('telegram_bot_fixed.py', 'telegram_bot_ultimate.py')
print("✅ telegram_bot_ultimate.py replaced with fixed version")

print("\nRestart bot: python run_fixed.py")