cat > analyze_project.py << 'EOF'
import os
import sys
from pathlib import Path
import json
import pickle
from datetime import datetime

def print_tree(directory, prefix="", max_depth=3, current_depth=0):
    """Печатает структуру директории"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(Path(directory).iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            
            if item.is_dir():
                print(f"{prefix}{current_prefix}{item.name}/")
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, max_depth, current_depth + 1)
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                print(f"{prefix}{current_prefix}{item.name} ({size_str})")
    except PermissionError:
        print(f"{prefix}{current_prefix}[Permission Denied]")

def analyze_file(filepath):
    """Анализирует содержимое файла"""
    result = {'type': 'unknown', 'size': filepath.stat().st_size if filepath.exists() else 0}
    
    try:
        if filepath.suffix == '.py':
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                classes = []
                functions = []
                for line in lines:
                    if line.startswith('class '):
                        classes.append(line.split('(')[0].replace('class ', '').strip())
                    elif line.startswith('def '):
                        func_name = line.split('(')[0].replace('def ', '').strip()
                        functions.append(func_name)
                result['type'] = 'python'
                result['lines'] = len(lines)
                result['classes'] = classes[:10]
                result['functions'] = functions[:10]
                
        elif filepath.suffix in ['.json', '.jsonl']:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result['type'] = 'json'
                if isinstance(data, list):
                    result['items'] = len(data)
                elif isinstance(data, dict):
                    result['keys'] = len(data.keys())
                    result['keys_list'] = list(data.keys())[:20]
                    
        elif filepath.suffix == '.pkl':
            try:
                with open(filepath, 'rb') as f:
                    data = pickle.load(f)
                    result['type'] = 'pickle'
                    result['data_type'] = type(data).__name__
            except Exception as e:
                result['type'] = 'pickle'
                result['error'] = 'Cannot load'
                
    except Exception as e:
        result['type'] = 'error'
        result['error'] = str(e)
    
    return result

# Основной анализ
print("=" * 100)
print("🔍 ПОЛНЫЙ АНАЛИЗ ПРОЕКТА")
print("=" * 100)

base_path = Path("C:/football_analytics_bot/football_finals/football_finals+Goal-Live")

if not base_path.exists():
    print(f"❌ Путь не найден: {base_path}")
    sys.exit(1)

print(f"\n📁 Проект: {base_path}")
print(f"📅 Анализ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Структура проекта
print("📂 СТРУКТУРА ПРОЕКТА:")
print("-" * 100)
print_tree(base_path, max_depth=4)
print()

# 2. Находим все Python файлы
print("🐍 PYTHON ФАЙЛЫ:")
print("-" * 100)
python_files = list(base_path.rglob("*.py"))
for py_file in sorted(python_files)[:30]:
    rel_path = py_file.relative_to(base_path)
    analysis = analyze_file(py_file)
    print(f"  📄 {rel_path} ({analysis.get('lines', '?')} строк)")
    if analysis.get('classes'):
        print(f"     Классы: {', '.join(analysis['classes'][:5])}")
    if analysis.get('functions'):
        print(f"     Функции: {', '.join(analysis['functions'][:5])}")
    print()

# 3. Проверяем данные
print("📊 ДАННЫЕ:")
print("-" * 100)

data_dir = base_path / "data"
if data_dir.exists():
    # Проверяем predictions
    pred_dir = data_dir / "predictions"
    if pred_dir.exists():
        pred_files = list(pred_dir.glob("*"))
        print(f"  📁 predictions/ ({len(pred_files)} файлов)")
        for pf in pred_files:
            analysis = analyze_file(pf)
            if analysis['type'] == 'json':
                if 'items' in analysis:
                    print(f"     📄 {pf.name}: {analysis['items']} записей")
                elif 'keys' in analysis:
                    print(f"     📄 {pf.name}: {analysis['keys']} ключей")
            else:
                print(f"     📄 {pf.name}: {analysis['size']} B")
    
    # Проверяем stats
    stats_dir = data_dir / "stats"
    if stats_dir.exists():
        stats_files = list(stats_dir.glob("*"))
        print(f"  📁 stats/ ({len(stats_files)} файлов)")
        for sf in stats_files[:10]:
            print(f"     📄 {sf.name} ({sf.stat().st_size} B)")
    
    # Проверяем logs
    logs_dir = data_dir / "logs"
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"  📁 logs/ ({len(log_files)} файлов)")
        for lf in log_files[-5:]:
            print(f"     📄 {lf.name} ({lf.stat().st_size} B)")
else:
    print("  ❌ data/ директория не найдена")

# 4. Проверяем модели
print("\n🤖 МОДЕЛИ:")
print("-" * 100)
models_dir = base_path / "models"
if models_dir.exists():
    model_files = list(models_dir.glob("*"))
    print(f"  📁 models/ ({len(model_files)} файлов)")
    for mf in model_files:
        analysis = analyze_file(mf)
        if analysis['type'] == 'pickle':
            print(f"     📄 {mf.name}: {analysis.get('data_type', 'unknown')}")
        elif analysis['type'] == 'json':
            print(f"     📄 {mf.name}: JSON модель")
        else:
            print(f"     📄 {mf.name}: {analysis['size']} B")
else:
    print("  ❌ models/ директория не найдена")

# 5. Проверяем конфигурацию
print("\n⚙️ КОНФИГУРАЦИЯ:")
print("-" * 100)
config_files = ['config.py', 'settings.py', '.env', 'config.json']
for cf in config_files:
    cf_path = base_path / cf
    if cf_path.exists():
        print(f"  ✅ {cf} найден")
        if cf == 'config.py':
            try:
                sys.path.insert(0, str(base_path))
                import config
                print(f"     USE_MOCK_API: {getattr(config.Config, 'USE_MOCK_API', 'N/A')}")
                print(f"     SAVE_PREDICTIONS: {getattr(config.Config, 'SAVE_PREDICTIONS', 'N/A')}")
                print(f"     TRAIN_AUTO: {getattr(config.Config, 'TRAIN_AUTO', 'N/A')}")
            except Exception as e:
                print(f"     ❌ Ошибка импорта: {e}")
    else:
        print(f"  ⚠️ {cf} не найден")

# 6. Проверяем основной бот
print("\n🤖 ОСНОВНОЙ БОТ:")
print("-" * 100)
main_files = ['main.py', 'bot.py', 'app.py', 'run.py']
for mf in main_files:
    mf_path = base_path / mf
    if mf_path.exists():
        print(f"  ✅ {mf} найден")
        with open(mf_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем ключевые слова
            if 'while True' in content:
                print("     🔄 Найден основной цикл")
            if 'save' in content.lower():
                print("     💾 Найдены операции сохранения")
            if 'train' in content.lower():
                print("     🎓 Найдены операции обучения")
            if 'threading' in content or 'Thread' in content:
                print("     🧵 Используются потоки")
    else:
        print(f"  ⚠️ {mf} не найден")

# 7. Анализ последних предсказаний
print("\n📈 АНАЛИЗ ПОСЛЕДНИХ ПРЕДСКАЗАНИЙ:")
print("-" * 100)
pred_file = base_path / "data/predictions/predictions.json"
if pred_file.exists():
    try:
        with open(pred_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        print(f"  📊 Всего предсказаний: {len(predictions)}")
        
        if len(predictions) > 0:
            # Последние 5 предсказаний
            print(f"\n  📋 Последние 5 предсказаний:")
            for i, pred in enumerate(predictions[-5:]):
                match_name = pred.get('match', 'N/A')
                minute = pred.get('minute', 'N/A')
                prediction = pred.get('prediction', 'N/A')
                status = pred.get('status', 'N/A')
                print(f"     {i+1}. {match_name} - {minute}' - Прогноз: {prediction} - Статус: {status}")
            
            # Статистика по статусам
            status_count = {}
            for pred in predictions:
                status = pred.get('status', 'unknown')
                status_count[status] = status_count.get(status, 0) + 1
            
            print(f"\n  📊 Статистика статусов:")
            for status, count in status_count.items():
                percentage = (count / len(predictions)) * 100
                print(f"     {status}: {count} ({percentage:.1f}%)")
    except Exception as e:
        print(f"  ❌ Ошибка чтения: {e}")
else:
    print("  ❌ predictions.json не найден")

# 8. Поиск ошибок в логах
print("\n🚨 ПОСЛЕДНИЕ ОШИБКИ ИЗ ЛОГОВ:")
print("-" * 100)
logs_dir = base_path / "data/logs"
if logs_dir.exists():
    log_files = list(logs_dir.glob("*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        print(f"  📄 Последний лог: {latest_log.name}")
        
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                error_lines = [l for l in lines if 'ERROR' in l or 'Exception' in l or 'failed' in l.lower()]
                
                if error_lines:
                    print(f"  🚨 Найдено ошибок: {len(error_lines)}")
                    print(f"\n  Последние 10 ошибок:")
                    for error in error_lines[-10:]:
                        print(f"     {error.strip()[:150]}")
                else:
                    print("  ✅ Ошибок не найдено")
        except Exception as e:
            print(f"  ❌ Ошибка чтения лога: {e}")
    else:
        print("  ⚠️ Лог-файлы не найдены")
else:
    print("  ⚠️ logs/ директория не найдена")

print("\n" + "=" * 100)
print("✅ АНАЛИЗ ЗАВЕРШЕН")
print("=" * 100)

EOF

python analyze_project.py