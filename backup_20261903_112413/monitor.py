# monitor.py
import time
import json
import os
from datetime import datetime

def check_bot_status():
    """Проверяет статус бота"""
    print("=" * 60)
    print("📊 МОНИТОРИНГ БОТА")
    print("=" * 60)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Проверяем сигналы
    if os.path.exists('signal_accuracy.json'):
        with open('signal_accuracy.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            stats = data.get('stats', {})
            print("📈 Статистика сигналов:")
            print(f"   • Всего: {stats.get('total_signals', 0)}")
            print(f"   • Точность: {stats.get('accuracy_rate', 0):.1f}%")
            print(f"   • Голов: {stats.get('goals_actual', 0)}")
    
    print()
    
    # Проверяем последние логи
    if os.path.exists('football_bot.log'):
        print("📋 Последние строки лога:")
        print("-" * 40)
        with open('football_bot.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()[-10:]
            for line in lines:
                print(line.strip())
        print("-" * 40)
    
    print()

if __name__ == "__main__":
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        check_bot_status()
        time.sleep(5)