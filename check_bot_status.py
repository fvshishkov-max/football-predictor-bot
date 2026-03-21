# check_bot_status.py
"""
Проверка состояния бота
Запуск: python check_bot_status.py
"""

import os
import sys
import json
from datetime import datetime

def check_bot_status():
    """Проверяет, что бот делает"""
    
    print("="*70)
    print("BOT STATUS CHECK")
    print("="*70)
    
    # 1. Проверяем лог
    print("\n1. LAST LOG ENTRIES:")
    print("-"*50)
    
    log_file = 'data/logs/app.log'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print("Last 10 lines:")
            for line in lines[-10:]:
                print(f"  {line.strip()}")
    else:
        print("  No log file found")
    
    # 2. Проверяем предсказания
    print("\n2. PREDICTIONS:")
    print("-"*50)
    
    pred_file = 'data/predictions/predictions.json'
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            predictions = data.get('predictions', [])
            print(f"  Total predictions: {len(predictions)}")
            
            if predictions:
                last = predictions[-1]
                print(f"  Last prediction: {last.get('timestamp', '')}")
                print(f"  Match: {last.get('home_team')} vs {last.get('away_team')}")
                print(f"  Minute: {last.get('minute')}")
                print(f"  Probability: {last.get('goal_probability', 0)*100:.1f}%")
    else:
        print("  No predictions file found")
    
    # 3. Проверяем время последнего обновления файла
    print("\n3. FILE MODIFICATION TIMES:")
    print("-"*50)
    
    if os.path.exists(pred_file):
        mtime = os.path.getmtime(pred_file)
        last_update = datetime.fromtimestamp(mtime)
        now = datetime.now()
        hours_ago = (now - last_update).total_seconds() / 3600
        print(f"  predictions.json last updated: {last_update.strftime('%H:%M:%S')} ({hours_ago:.1f} hours ago)")
    
    if os.path.exists(log_file):
        mtime = os.path.getmtime(log_file)
        last_update = datetime.fromtimestamp(mtime)
        now = datetime.now()
        hours_ago = (now - last_update).total_seconds() / 3600
        print(f"  app.log last updated: {last_update.strftime('%H:%M:%S')} ({hours_ago:.1f} hours ago)")
    
    # 4. Рекомендации
    print("\n4. RECOMMENDATIONS:")
    print("-"*50)
    
    if len(predictions) == 10:
        print("  • No new predictions in the last hour")
        print("  • Possible reasons:")
        print("    1. No live matches at the moment")
        print("    2. API connection issues")
        print("    3. Bot not receiving data")
        print("\n  • What to do:")
        print("    1. Check if there are live matches now")
        print("    2. Restart the bot: python run_fixed.py")
        print("    3. Check API keys in config.py")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    check_bot_status()