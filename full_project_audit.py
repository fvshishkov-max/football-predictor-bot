# full_project_audit.py
"""
Полная проверка всех файлов и путей в проекте
Запуск: python full_project_audit.py
"""

import os
import sys
import json
import glob
from datetime import datetime

def audit():
    print("="*80)
    print("FULL PROJECT AUDIT")
    print("="*80)
    
    # 1. Проверка структуры папок
    print("\n1. FOLDER STRUCTURE:")
    print("-"*60)
    
    required_folders = [
        'data',
        'data/predictions',
        'data/history',
        'data/stats',
        'data/logs',
        'data/backups',
        'data/models',
        'data/cache'
    ]
    
    for folder in required_folders:
        if os.path.exists(folder):
            print(f"  [OK] {folder}/")
        else:
            print(f"  [MISSING] {folder}/")
    
    # 2. Проверка основных файлов
    print("\n2. CORE FILES:")
    print("-"*60)
    
    core_files = [
        'run_fixed.py', 'app.py', 'predictor.py', 'telegram_bot.py',
        'stats_reporter.py', 'translations.py', 'api_client.py',
        'models.py', 'config.py', 'team_form.py', 'match_analyzer.py'
    ]
    
    for file in core_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  [OK] {file} ({size} bytes)")
        else:
            print(f"  [MISSING] {file}")
    
    # 3. Проверка файлов данных
    print("\n3. DATA FILES:")
    print("-"*60)
    
    data_files = {
        'data/predictions/predictions.json': 'Predictions',
        'data/predictions/predictions_test.json': 'Test predictions',
        'data/logs/app.log': 'Log file',
        'data/stats/prediction_stats.json': 'Statistics'
    }
    
    for file, desc in data_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            print(f"  [OK] {desc}: {file} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
        else:
            print(f"  [MISSING] {desc}: {file}")
    
    # 4. Проверка содержимого predictions.json
    print("\n4. PREDICTIONS.JSON CONTENT:")
    print("-"*60)
    
    pred_file = 'data/predictions/predictions.json'
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            predictions = data.get('predictions', [])
            stats = data.get('accuracy_stats', {})
            
            print(f"  Total predictions: {len(predictions)}")
            print(f"  Correct: {stats.get('correct_predictions', 0)}")
            print(f"  Incorrect: {stats.get('incorrect_predictions', 0)}")
            print(f"  Accuracy: {stats.get('accuracy_rate', 0)*100:.1f}%")
            
            if predictions:
                print("\n  Last 5 predictions:")
                for pred in predictions[-5:]:
                    ts = pred.get('timestamp', '')[:19]
                    home = pred.get('home_team', '?')
                    away = pred.get('away_team', '?')
                    prob = pred.get('goal_probability', 0) * 100
                    minute = pred.get('minute', 0)
                    was_correct = pred.get('was_correct')
                    status = "✓" if was_correct else ("✗" if was_correct is False else "?")
                    print(f"    {ts} | {minute}' | {home} vs {away} | {prob:.1f}% | {status}")
    else:
        print("  File not found!")
    
    # 5. Проверка логов
    print("\n5. LOG FILE CONTENT:")
    print("-"*60)
    
    log_file = 'data/logs/app.log'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"  Total lines: {len(lines)}")
            if lines:
                print("\n  Last 5 lines:")
                for line in lines[-5:]:
                    print(f"    {line.strip()}")
    else:
        print("  No log file")
    
    # 6. Проверка Python процессов
    print("\n6. PYTHON PROCESSES:")
    print("-"*60)
    
    try:
        import psutil
        python_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'run_fixed.py' in cmdline or 'monitor' in cmdline:
                        start_time = datetime.fromtimestamp(proc.info['create_time'])
                        python_procs.append((proc.info['pid'], cmdline[:80], start_time))
            except:
                pass
        
        if python_procs:
            for pid, cmd, start in python_procs:
                print(f"  PID {pid}: {cmd} (started: {start.strftime('%H:%M:%S')})")
        else:
            print("  No Python processes found")
    except ImportError:
        print("  psutil not installed, run: pip install psutil")
    
    # 7. Проверка последних изменений
    print("\n7. RECENT FILE CHANGES (last 30 min):")
    print("-"*60)
    
    now = datetime.now()
    for file in glob.glob('data/predictions/*.json') + ['data/logs/app.log']:
        if os.path.exists(file):
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            minutes_ago = (now - mtime).total_seconds() / 60
            if minutes_ago < 30:
                print(f"  Updated: {file} ({minutes_ago:.0f} min ago)")
    
    # 8. Рекомендации
    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    
    if len(predictions) < 10:
        print("  • Very few predictions - bot may not be generating new ones")
        print("  • Check if bot is properly connected to API")
        print("  • Verify there are live matches")
    
    if len(lines) < 10:
        print("  • Log file has few entries - logging may not work")
        print("  • Check that logger is configured correctly")
    
    print("\n  To get more predictions:")
    print("    1. Restart bot: python run_fixed.py")
    print("    2. Check API keys in config.py")
    print("    3. Monitor logs: type data\\logs\\app.log")
    
    print("="*80)

if __name__ == "__main__":
    audit()