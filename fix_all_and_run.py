# fix_all_and_run.py
"""
Исправление всех файлов и запуск бота
Запуск: python fix_all_and_run.py
"""

import os
import sys
import subprocess
import time

def run_command(cmd):
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result

def main():
    print("="*70)
    print("🔧 ИСПРАВЛЕНИЕ ВСЕХ ФАЙЛОВ")
    print("="*70)
    
    # Создаем исправленные файлы
    print("\n1. Исправление match_analyzer.py...")
    run_command("python fix_match_analyzer.py")
    
    print("\n2. Исправление signal_validator.py...")
    run_command("python fix_signal_validator.py")
    
    print("\n3. Создание финального predictor.py...")
    run_command("python create_final_predictor.py")
    
    print("\n4. Запуск бота...")
    print("="*70)
    time.sleep(2)
    
    run_command("python run_fixed.py")

if __name__ == "__main__":
    main()