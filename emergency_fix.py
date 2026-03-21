# emergency_fix.py
"""
Экстренное восстановление predictor.py из резервной копии
"""

import os
import shutil

# Ищем бэкап
backup_files = [f for f in os.listdir('.') if f.startswith('predictor.py.backup') or f == 'predictor.py.bak']

if backup_files:
    print(f"Found backup: {backup_files[0]}")
    shutil.copy(backup_files[0], 'predictor.py')
    print("✅ Restored from backup")
else:
    print("No backup found. Please provide a working predictor.py")

print("\nNow run: python run_fixed.py")