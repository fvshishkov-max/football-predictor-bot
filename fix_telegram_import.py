# fix_telegram_import.py
"""
Замена импорта в app.py для использования прямой версии
"""

import os
import shutil

# Сохраняем старую версию
if os.path.exists('telegram_bot_ultimate.py'):
    shutil.copy('telegram_bot_ultimate.py', 'telegram_bot_ultimate_old.py')
    print("✅ Backup created: telegram_bot_ultimate_old.py")

# Копируем прямую версию
shutil.copy('telegram_bot_direct.py', 'telegram_bot_ultimate.py')
print("✅ Replaced with direct version")

print("\nNow restart bot: python run_fixed.py")