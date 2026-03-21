# global_project_audit.py
"""
Глобальная проверка файловой системы и логики сохранения предсказаний
Запуск: python global_project_audit.py
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime
from pathlib import Path

def audit_project():
    print("="*80)
    print("🌍 ГЛОБАЛЬНЫЙ АУДИТ ПРОЕКТА")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    issues = []
    warnings = []
    
    # 1. ПРОВЕРКА СТРУКТУРЫ ПАПОК
    print("\n1. ПРОВЕРКА СТРУКТУРЫ ПАПОК:")
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
            print(f"  ✅ {folder}/")
        else:
            print(f"  ❌ {folder}/ - ОТСУТСТВУЕТ!")
            issues.append(f"Отсутствует папка: {folder}")
    
    # 2. ПРОВЕРКА ФАЙЛОВ ПРЕДСКАЗАНИЙ
    print("\n2. ПРОВЕРКА ФАЙЛОВ ПРЕДСКАЗАНИЙ:")
    print("-"*60)
    
    pred_files = [
        'data/predictions/predictions.json',
        'data/predictions.json',
        'predictions.json'
    ]
    
    for file in pred_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            print(f"  ✅ {file} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
            
            # Проверяем содержимое
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    preds = data.get('predictions', [])
                    print(f"     Предсказаний: {len(preds)}")
                    
                    if preds:
                        last = preds[-1]
                        print(f"     Последнее: {last.get('timestamp', '')[:19]} - {last.get('home_team')} vs {last.get('away_team')}")
                        print(f"     Вероятность: {last.get('goal_probability', 0)*100:.1f}%")
                        print(f"     Результат: {last.get('was_correct', '❓')}")
                    else:
                        warnings.append(f"Файл {file} пуст")
            except Exception as e:
                print(f"     ❌ Ошибка чтения: {e}")
                issues.append(f"Ошибка чтения {file}: {e}")
        else:
            print(f"  ⚠️ {file} - НЕ НАЙДЕН")
    
    # 3. ПРОВЕРКА ФАЙЛОВ В HISTORY
    print("\n3. ПРОВЕРКА ПАПКИ HISTORY:")
    print("-"*60)
    
    history_dir = 'data/history'
    if os.path.exists(history_dir):
        files = os.listdir(history_dir)
        print(f"  Всего файлов: {len(files)}")
        
        csv_files = [f for f in files if f.endswith('.csv')]
        db_files = [f for f in files if f.endswith('.db')]
        
        print(f"  CSV файлов: {len(csv_files)}")
        print(f"  DB файлов: {len(db_files)}")
        
        if csv_files:
            latest_csv = sorted(csv_files)[-5:]
            print(f"  Последние CSV файлы:")
            for f in latest_csv:
                size = os.path.getsize(os.path.join(history_dir, f))
                print(f"    • {f} ({size} bytes)")
    else:
        print("  ❌ Папка history не найдена")
    
    # 4. ПРОВЕРКА ЛОГОВ
    print("\n4. ПРОВЕРКА ЛОГОВ:")
    print("-"*60)
    
    log_files = [
        'data/logs/app.log',
        'app.log',
        'bot.log'
    ]
    
    for log in log_files:
        if os.path.exists(log):
            size = os.path.getsize(log)
            mtime = datetime.fromtimestamp(os.path.getmtime(log))
            print(f"  ✅ {log} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
            
            # Показываем последние строки
            try:
                with open(log, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"     Последние 3 строки:")
                        for line in lines[-3:]:
                            print(f"       {line.strip()[:100]}")
            except Exception as e:
                print(f"     ⚠️ Не удалось прочитать: {e}")
        else:
            print(f"  ⚠️ {log} - НЕ НАЙДЕН")
            warnings.append(f"Лог-файл {log} отсутствует")
    
    # 5. ПРОВЕРКА ПРОЦЕССОВ
    print("\n5. ПРОВЕРКА ПРОЦЕССОВ:")
    print("-"*60)
    
    try:
        import psutil
        python_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'run_fixed.py' in cmdline or 'continuous' in cmdline or 'monitor' in cmdline:
                        start_time = datetime.fromtimestamp(proc.info['create_time'])
                        python_procs.append({
                            'pid': proc.info['pid'],
                            'cmd': cmdline[:80],
                            'start': start_time
                        })
            except:
                pass
        
        if python_procs:
            print(f"  Найдено Python процессов: {len(python_procs)}")
            for p in python_procs:
                print(f"    • PID {p['pid']}: {p['cmd']} (с {p['start'].strftime('%H:%M:%S')})")
        else:
            print("  ❌ Нет Python процессов")
            warnings.append("Бот не запущен")
    except ImportError:
        print("  ⚠️ psutil не установлен")
    
    # 6. ПРОВЕРКА АКТИВНОСТИ ЗАПИСИ
    print("\n6. ПРОВЕРКА АКТИВНОСТИ ЗАПИСИ:")
    print("-"*60)
    
    pred_file = 'data/predictions/predictions.json'
    if os.path.exists(pred_file):
        mtime = os.path.getmtime(pred_file)
        last_write = datetime.fromtimestamp(mtime)
        now = datetime.now()
        minutes_ago = (now - last_write).total_seconds() / 60
        
        if minutes_ago < 10:
            print(f"  ✅ Файл обновлен {minutes_ago:.0f} минут назад")
        else:
            print(f"  ⚠️ Файл НЕ ОБНОВЛЯЕТСЯ! Последнее обновление {minutes_ago:.0f} минут назад")
            warnings.append(f"Файл predictions.json не обновляется с {last_write.strftime('%H:%M:%S')}")
    
    # 7. ПРОВЕРКА МЕТОДОВ СОХРАНЕНИЯ
    print("\n7. ПРОВЕРКА МЕТОДОВ СОХРАНЕНИЯ:")
    print("-"*60)
    
    # Проверяем predictor.py
    if os.path.exists('predictor.py'):
        with open('predictor.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        save_calls = content.count('save_predictions()')
        print(f"  save_predictions() вызовов: {save_calls}")
        
        if save_calls == 0:
            issues.append("Нет вызовов save_predictions в predictor.py")
        
        # Проверяем, вызывается ли после каждого прогноза
        if 'self.save_predictions()' in content:
            print("  ✅ Вызов save_predictions найден")
        else:
            print("  ❌ Вызов save_predictions НЕ НАЙДЕН")
            issues.append("Отсутствует вызов save_predictions")
    
    # 8. ПРОВЕРКА КОНФИГУРАЦИИ
    print("\n8. ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("-"*60)
    
    if os.path.exists('config.py'):
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем пути
        if 'PREDICTIONS_FILE' in content:
            print("  ✅ PREDICTIONS_FILE определен")
        else:
            print("  ❌ PREDICTIONS_FILE НЕ ОПРЕДЕЛЕН")
            issues.append("PREDICTIONS_FILE не в config.py")
        
        if 'MIN_PROBABILITY_FOR_SIGNAL' in content:
            print("  ✅ MIN_PROBABILITY_FOR_SIGNAL определен")
        else:
            print("  ❌ MIN_PROBABILITY_FOR_SIGNAL НЕ ОПРЕДЕЛЕН")
    
    # 9. ПРОВЕРКА XGBOOST
    print("\n9. ПРОВЕРКА XGBOOST:")
    print("-"*60)
    
    model_files = [
        'data/models/xgboost_model.pkl',
        'xgboost_model.pkl'
    ]
    
    for model in model_files:
        if os.path.exists(model):
            size = os.path.getsize(model)
            mtime = datetime.fromtimestamp(os.path.getmtime(model))
            print(f"  ✅ {model} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
        else:
            print(f"  ⚠️ {model} - НЕ НАЙДЕН")
            warnings.append(f"Модель XGBoost не найдена")
    
    # 10. ИТОГИ
    print("\n" + "="*80)
    print("📊 ИТОГИ АУДИТА")
    print("="*80)
    
    print(f"\n✅ Успешно: {len(required_folders)} папок")
    print(f"⚠️ Предупреждений: {len(warnings)}")
    print(f"❌ Проблем: {len(issues)}")
    
    if issues:
        print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  • {warning}")
    
    # 11. РЕКОМЕНДАЦИИ
    print("\n" + "="*80)
    print("💡 РЕКОМЕНДАЦИИ:")
    print("="*80)
    
    if len(issues) > 0:
        print("\n  1. СРОЧНО ИСПРАВИТЬ:")
        print("     • Добавить вызов save_predictions() после каждого прогноза")
        print("     • Проверить пути сохранения в config.py")
        print("     • Убедиться, что бот запущен и получает live матчи")
    
    if len(python_procs) == 0:
        print("\n  2. ЗАПУСТИТЬ БОТА:")
        print("     python run_fixed.py")
    
    print("\n  3. ДЛЯ ОТЛАДКИ:")
    print("     • Запустить: python continuous_check.py")
    print("     • Следить за логами: type data\\logs\\app.log")
    print("     • Проверить API: python test_api_now.py")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    audit_project()