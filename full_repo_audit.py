# full_repo_audit.py
"""
Полный аудит репозитория: проверка всех файлов и структуры сохранения данных
Запуск: python full_repo_audit.py
"""

import os
import sys
import json
import sqlite3
import importlib
from datetime import datetime
from pathlib import Path

def audit_repository():
    """Полный аудит репозитория"""
    
    print("="*80)
    print("🔍 ПОЛНЫЙ АУДИТ РЕПОЗИТОРИЯ")
    print("="*80)
    
    issues = []
    warnings = []
    ok_count = 0
    
    # ============================================
    # 1. ПРОВЕРКА ОСНОВНЫХ ФАЙЛОВ
    # ============================================
    print("\n1. ПРОВЕРКА ОСНОВНЫХ ФАЙЛОВ:")
    print("-"*60)
    
    core_files = [
        'run_fixed.py', 'app.py', 'predictor.py', 'telegram_bot.py',
        'stats_reporter.py', 'translations.py', 'api_client.py',
        'models.py', 'config.py', 'team_form.py', 'betting_optimizer.py',
        'feature_engineering.py', 'statistical_models.py', 'advanced_features.py',
        'match_analyzer.py', 'signal_validator.py'
    ]
    
    for file in core_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file} ({size} bytes)")
            ok_count += 1
        else:
            print(f"  ❌ {file} - ОТСУТСТВУЕТ!")
            issues.append(f"Отсутствует файл: {file}")
    
    # ============================================
    # 2. ПРОВЕРКА КОНФИГУРАЦИИ
    # ============================================
    print("\n2. ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("-"*60)
    
    # Проверяем config.py
    if os.path.exists('config.py'):
        try:
            import config
            print(f"  ✅ config.py загружен")
            print(f"    • TELEGRAM_TOKEN: {'SET' if config.TELEGRAM_TOKEN else 'EMPTY'}")
            print(f"    • CHANNEL_ID: {config.CHANNEL_ID}")
            print(f"    • DATA_DIR: {config.DATA_DIR}")
            print(f"    • PREDICTIONS_FILE: {config.PREDICTIONS_FILE}")
        except Exception as e:
            print(f"  ❌ Ошибка импорта config.py: {e}")
            issues.append(f"Ошибка конфигурации: {e}")
    else:
        issues.append("config.py не найден")
    
    # ============================================
    # 3. ПРОВЕРКА СТРУКТУРЫ ПАПОК
    # ============================================
    print("\n3. ПРОВЕРКА СТРУКТУРЫ ПАПОК:")
    print("-"*60)
    
    folders = [
        'data',
        'data/predictions',
        'data/history',
        'data/stats',
        'data/logs',
        'data/backups',
        'data/models',
        'data/cache',
        'analytics',
        'tools',
        'scripts'
    ]
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"  ✅ {folder}/")
            ok_count += 1
        else:
            print(f"  ❌ {folder}/ - ОТСУТСТВУЕТ!")
            issues.append(f"Отсутствует папка: {folder}")
    
    # ============================================
    # 4. ПРОВЕРКА ФАЙЛОВ ДАННЫХ
    # ============================================
    print("\n4. ПРОВЕРКА ФАЙЛОВ ДАННЫХ:")
    print("-"*60)
    
    data_files = {
        'data/predictions/predictions.json': 'Предсказания',
        'data/stats/prediction_stats.json': 'Статистика',
        'data/history/matches_history.db': 'База данных матчей',
        'data/models/xgboost_model.pkl': 'Модель XGBoost',
        'data/logs/app.log': 'Лог приложения'
    }
    
    for file, description in data_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            print(f"  ✅ {description}: {file} ({size} bytes, {mod_time.strftime('%Y-%m-%d %H:%M')})")
            ok_count += 1
        else:
            print(f"  ⚠️ {description}: {file} - НЕ НАЙДЕН")
            warnings.append(f"Файл данных не найден: {file}")
    
    # ============================================
    # 5. ПРОВЕРКА СОДЕРЖИМОГО PREDICTIONS.JSON
    # ============================================
    print("\n5. ПРОВЕРКА СОДЕРЖИМОГО PREDICTIONS.JSON:")
    print("-"*60)
    
    predictions_paths = [
        'data/predictions/predictions.json',
        'data/predictions.json'
    ]
    
    total_predictions = 0
    for path in predictions_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                predictions = data.get('predictions', [])
                stats = data.get('accuracy_stats', {})
                print(f"\n  📄 {path}:")
                print(f"    • Предсказаний: {len(predictions)}")
                print(f"    • Всего в статистике: {stats.get('total_predictions', 0)}")
                print(f"    • Правильных: {stats.get('correct_predictions', 0)}")
                print(f"    • Точность: {stats.get('accuracy_rate', 0)*100:.1f}%")
                total_predictions += len(predictions)
                
                # Показываем последние 5 предсказаний
                if predictions:
                    print(f"\n    📋 Последние 5 предсказаний:")
                    for pred in predictions[-5:]:
                        ts = pred.get('timestamp', '')[:19]
                        home = pred.get('home_team', '?')
                        away = pred.get('away_team', '?')
                        prob = pred.get('goal_probability', 0) * 100
                        was_correct = pred.get('was_correct', '?')
                        correct_mark = "✅" if was_correct else ("❌" if was_correct is False else "❓")
                        print(f"      {ts} | {correct_mark} | {home} vs {away} | {prob:.1f}%")
                        
            except Exception as e:
                print(f"  ❌ Ошибка чтения {path}: {e}")
                issues.append(f"Ошибка чтения {path}: {e}")
    
    # ============================================
    # 6. ПРОВЕРКА CSV ФАЙЛОВ В HISTORY
    # ============================================
    print("\n6. ПРОВЕРКА CSV ФАЙЛОВ В data/history/:")
    print("-"*60)
    
    if os.path.exists('data/history'):
        csv_files = [f for f in os.listdir('data/history') if f.endswith('.csv')]
        if csv_files:
            for csv_file in csv_files[:5]:  # Показываем первые 5
                path = os.path.join('data/history', csv_file)
                size = os.path.getsize(path)
                print(f"  📄 {csv_file} ({size} bytes)")
            
            if len(csv_files) > 5:
                print(f"  ... и еще {len(csv_files)-5} CSV файлов")
            
            print(f"\n  ⚠️ ВНИМАНИЕ: Найдено {len(csv_files)} CSV файлов!")
            print(f"     Это архивные данные. Актуальные предсказания должны быть в predictions.json")
            warnings.append(f"Найдено {len(csv_files)} CSV файлов в data/history - возможно, это дубликаты")
        else:
            print(f"  ✅ CSV файлов не найдено")
    
    # ============================================
    # 7. ПРОВЕРКА МЕТОДА СОХРАНЕНИЯ В PREDICTOR.PY
    # ============================================
    print("\n7. ПРОВЕРКА МЕТОДА СОХРАНЕНИЯ В PREDICTOR.PY:")
    print("-"*60)
    
    if os.path.exists('predictor.py'):
        with open('predictor.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие метода save_predictions
        if 'def save_predictions' in content:
            print(f"  ✅ Метод save_predictions найден")
            
            # Проверяем правильный путь
            if "filename: str = 'data/predictions/predictions.json'" in content:
                print(f"  ✅ Путь сохранения: data/predictions/predictions.json")
            elif "filename: str = 'predictions.json'" in content:
                print(f"  ⚠️ Путь сохранения: predictions.json (старый формат)")
                warnings.append("predictor.py использует старый путь сохранения")
            else:
                print(f"  ℹ️ Путь сохранения не стандартный")
        else:
            print(f"  ❌ Метод save_predictions НЕ НАЙДЕН!")
            issues.append("Метод save_predictions отсутствует в predictor.py")
        
        # Проверяем вызов save_predictions
        if 'self.save_predictions()' in content:
            print(f"  ✅ Вызов save_predictions найден")
        else:
            print(f"  ⚠️ Вызов save_predictions НЕ НАЙДЕН")
            warnings.append("Нет вызова save_predictions в predictor.py")
    
    # ============================================
    # 8. ПРОВЕРКА МЕТОДА СОХРАНЕНИЯ В STATS_REPORTER.PY
    # ============================================
    print("\n8. ПРОВЕРКА МЕТОДА СОХРАНЕНИЯ В STATS_REPORTER.PY:")
    print("-"*60)
    
    if os.path.exists('stats_reporter.py'):
        with open('stats_reporter.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def save_stats' in content:
            print(f"  ✅ Метод save_stats найден")
        else:
            print(f"  ❌ Метод save_stats НЕ НАЙДЕН")
            issues.append("Метод save_stats отсутствует в stats_reporter.py")
        
        # Проверяем вызов save_stats
        if 'self.save_stats()' in content:
            print(f"  ✅ Вызов save_stats найден")
        else:
            print(f"  ⚠️ Вызов save_stats НЕ НАЙДЕН")
            warnings.append("Нет вызова save_stats в stats_reporter.py")
    
    # ============================================
    # 9. ПРОВЕРКА ТЕКУЩЕЙ СЕССИИ
    # ============================================
    print("\n9. ПРОВЕРКА ТЕКУЩЕЙ СЕССИИ (live):")
    print("-"*60)
    
    # Проверяем наличие PID файла
    if os.path.exists('bot.pid'):
        with open('bot.pid', 'r') as f:
            pid = f.read().strip()
        print(f"  ℹ️ Бот может быть запущен (PID: {pid})")
    else:
        print(f"  ℹ️ Бот не запущен (нет PID файла)")
    
    # ============================================
    # 10. ИТОГОВЫЙ ОТЧЕТ
    # ============================================
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ ОТЧЕТ АУДИТА")
    print("="*80)
    
    print(f"\n✅ Успешно проверено: {ok_count} элементов")
    print(f"⚠️ Предупреждений: {len(warnings)}")
    print(f"❌ Проблем: {len(issues)}")
    
    if issues:
        print("\n❌ СПИСОК ПРОБЛЕМ:")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print("\n⚠️ СПИСОК ПРЕДУПРЕЖДЕНИЙ:")
        for warning in warnings:
            print(f"  • {warning}")
    
    print(f"\n📊 ВСЕГО АКТУАЛЬНЫХ ПРЕДСКАЗАНИЙ: {total_predictions}")
    
    if total_predictions < 10:
        print("\n🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА: Мало актуальных предсказаний!")
        print("   Возможные причины:")
        print("   1. Бот не запущен или работает нестабильно")
        print("   2. Предсказания не сохраняются (проблема с save_predictions)")
        print("   3. Данные сохраняются в другом месте")
        print("   4. CSV файлы содержат архив, а новые данные не пишутся")
    
    print("\n" + "="*80)
    print("💡 РЕКОМЕНДАЦИИ:")
    print("-"*60)
    print("  1. Запустите бота: python run_fixed.py")
    print("  2. Проверьте, создаются ли новые записи в data/predictions/predictions.json")
    print("  3. Убедитесь, что в predictor.py вызывается save_predictions() после каждого прогноза")
    print("  4. Проверьте логи в data/logs/app.log на наличие ошибок")
    print("  5. Если нужно, перенесите старые данные из CSV в predictions.json")
    print("="*80)
    
    return issues, warnings, total_predictions

if __name__ == "__main__":
    audit_repository()