# Сначала удалим старый файл, если есть
del analyze_project.py

# Теперь создадим новый файл правильно
echo import os > analyze_project.py
echo import sys >> analyze_project.py
echo from pathlib import Path >> analyze_project.py
echo import json >> analyze_project.py
echo import pickle >> analyze_project.py
echo from datetime import datetime >> analyze_project.py
echo. >> analyze_project.py
echo def print_tree(directory, prefix="", max_depth=3, current_depth=0): >> analyze_project.py
echo     if current_depth >= max_depth: >> analyze_project.py
echo         return >> analyze_project.py
echo     try: >> analyze_project.py
echo         items = sorted(Path(directory).iterdir()) >> analyze_project.py
echo         for i, item in enumerate(items): >> analyze_project.py
echo             is_last = i == len(items) - 1 >> analyze_project.py
echo             current_prefix = "└── " if is_last else "├── " >> analyze_project.py
echo             if item.is_dir(): >> analyze_project.py
echo                 print(f"{prefix}{current_prefix}{item.name}/") >> analyze_project.py
echo                 extension = "    " if is_last else "│   " >> analyze_project.py
echo                 print_tree(item, prefix + extension, max_depth, current_depth + 1) >> analyze_project.py
echo             else: >> analyze_project.py
echo                 size = item.stat().st_size >> analyze_project.py
echo                 if size ^< 1024: >> analyze_project.py
echo                     size_str = f"{size} B" >> analyze_project.py
echo                 elif size ^< 1024*1024: >> analyze_project.py
echo                     size_str = f"{size/1024:.1f} KB" >> analyze_project.py
echo                 else: >> analyze_project.py
echo                     size_str = f"{size/(1024*1024):.1f} MB" >> analyze_project.py
echo                 print(f"{prefix}{current_prefix}{item.name} ({size_str})") >> analyze_project.py
echo     except PermissionError: >> analyze_project.py
echo         print(f"{prefix}{current_prefix}[Permission Denied]") >> analyze_project.py
echo. >> analyze_project.py
echo def analyze_file(filepath): >> analyze_project.py
echo     result = {'type': 'unknown', 'size': filepath.stat().st_size if filepath.exists() else 0} >> analyze_project.py
echo     try: >> analyze_project.py
echo         if filepath.suffix == '.py': >> analyze_project.py
echo             with open(filepath, 'r', encoding='utf-8') as f: >> analyze_project.py
echo                 content = f.read() >> analyze_project.py
echo                 lines = content.split('\n') >> analyze_project.py
echo                 classes = [] >> analyze_project.py
echo                 functions = [] >> analyze_project.py
echo                 for line in lines: >> analyze_project.py
echo                     if line.startswith('class '): >> analyze_project.py
echo                         classes.append(line.split('(')[0].replace('class ', '').strip()) >> analyze_project.py
echo                     elif line.startswith('def '): >> analyze_project.py
echo                         func_name = line.split('(')[0].replace('def ', '').strip() >> analyze_project.py
echo                         functions.append(func_name) >> analyze_project.py
echo                 result['type'] = 'python' >> analyze_project.py
echo                 result['lines'] = len(lines) >> analyze_project.py
echo                 result['classes'] = classes[:10] >> analyze_project.py
echo                 result['functions'] = functions[:10] >> analyze_project.py
echo         elif filepath.suffix in ['.json', '.jsonl']: >> analyze_project.py
echo             with open(filepath, 'r', encoding='utf-8') as f: >> analyze_project.py
echo                 data = json.load(f) >> analyze_project.py
echo                 result['type'] = 'json' >> analyze_project.py
echo                 if isinstance(data, list): >> analyze_project.py
echo                     result['items'] = len(data) >> analyze_project.py
echo                 elif isinstance(data, dict): >> analyze_project.py
echo                     result['keys'] = len(data.keys()) >> analyze_project.py
echo                     result['keys_list'] = list(data.keys())[:20] >> analyze_project.py
echo         elif filepath.suffix == '.pkl': >> analyze_project.py
echo             try: >> analyze_project.py
echo                 with open(filepath, 'rb') as f: >> analyze_project.py
echo                     data = pickle.load(f) >> analyze_project.py
echo                     result['type'] = 'pickle' >> analyze_project.py
echo                     result['data_type'] = type(data).__name__ >> analyze_project.py
echo             except Exception as e: >> analyze_project.py
echo                 result['type'] = 'pickle' >> analyze_project.py
echo                 result['error'] = 'Cannot load' >> analyze_project.py
echo     except Exception as e: >> analyze_project.py
echo         result['type'] = 'error' >> analyze_project.py
echo         result['error'] = str(e) >> analyze_project.py
echo     return result >> analyze_project.py
echo. >> analyze_project.py
echo print("=" * 100) >> analyze_project.py
echo print("🔍 ПОЛНЫЙ АНАЛИЗ ПРОЕКТА") >> analyze_project.py
echo print("=" * 100) >> analyze_project.py
echo base_path = Path("C:/football_analytics_bot/football_finals/football_finals+Goal-Live") >> analyze_project.py
echo if not base_path.exists(): >> analyze_project.py
echo     print(f"❌ Путь не найден: {base_path}") >> analyze_project.py
echo     sys.exit(1) >> analyze_project.py
echo print(f"\n📁 Проект: {base_path}") >> analyze_project.py
echo print(f"📅 Анализ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") >> analyze_project.py
echo print() >> analyze_project.py
echo print("📂 СТРУКТУРА ПРОЕКТА:") >> analyze_project.py
echo print("-" * 100) >> analyze_project.py
echo print_tree(base_path, max_depth=3) >> analyze_project.py
echo print() >> analyze_project.py
echo print("🐍 PYTHON ФАЙЛЫ:") >> analyze_project.py
echo print("-" * 100) >> analyze_project.py
echo python_files = list(base_path.rglob("*.py")) >> analyze_project.py
echo for py_file in sorted(python_files)[:20]: >> analyze_project.py
echo     rel_path = py_file.relative_to(base_path) >> analyze_project.py
echo     analysis = analyze_file(py_file) >> analyze_project.py
echo     print(f"  📄 {rel_path} ({analysis.get('lines', '?')} строк)") >> analyze_project.py
echo     if analysis.get('classes'): >> analyze_project.py
echo         print(f"     Классы: {', '.join(analysis['classes'][:3])}") >> analyze_project.py
echo     if analysis.get('functions'): >> analyze_project.py
echo         print(f"     Функции: {', '.join(analysis['functions'][:3])}") >> analyze_project.py
echo     print() >> analyze_project.py
echo print("📊 ДАННЫЕ:") >> analyze_project.py
echo print("-" * 100) >> analyze_project.py
echo data_dir = base_path / "data" >> analyze_project.py
echo if data_dir.exists(): >> analyze_project.py
echo     pred_dir = data_dir / "predictions" >> analyze_project.py
echo     if pred_dir.exists(): >> analyze_project.py
echo         pred_files = list(pred_dir.glob("*")) >> analyze_project.py
echo         print(f"  📁 predictions/ ({len(pred_files)} файлов)") >> analyze_project.py
echo         for pf in pred_files: >> analyze_project.py
echo             analysis = analyze_file(pf) >> analyze_project.py
echo             if analysis['type'] == 'json': >> analyze_project.py
echo                 if 'items' in analysis: >> analyze_project.py
echo                     print(f"     📄 {pf.name}: {analysis['items']} записей") >> analyze_project.py
echo                 else: >> analyze_project.py
echo                     print(f"     📄 {pf.name}: {analysis['size']} B") >> analyze_project.py
echo             else: >> analyze_project.py
echo                 print(f"     📄 {pf.name}: {analysis['size']} B") >> analyze_project.py
echo else: >> analyze_project.py
echo     print("  ❌ data/ не найдена") >> analyze_project.py
echo print("\n🤖 МОДЕЛИ:") >> analyze_project.py
echo print("-" * 100) >> analyze_project.py
echo models_dir = base_path / "models" >> analyze_project.py
echo if models_dir.exists(): >> analyze_project.py
echo     model_files = list(models_dir.glob("*")) >> analyze_project.py
echo     print(f"  📁 models/ ({len(model_files)} файлов)") >> analyze_project.py
echo     for mf in model_files: >> analyze_project.py
echo         analysis = analyze_file(mf) >> analyze_project.py
echo         print(f"     📄 {mf.name}: {analysis.get('data_type', 'unknown')}") >> analyze_project.py
echo else: >> analyze_project.py
echo     print("  ❌ models/ не найдена") >> analyze_project.py
echo print("\n📈 АНАЛИЗ ПРЕДСКАЗАНИЙ:") >> analyze_project.py
echo print("-" * 100) >> analyze_project.py
echo pred_file = base_path / "data/predictions/predictions.json" >> analyze_project.py
echo if pred_file.exists(): >> analyze_project.py
echo     try: >> analyze_project.py
echo         with open(pred_file, 'r', encoding='utf-8') as f: >> analyze_project.py
echo             predictions = json.load(f) >> analyze_project.py
echo         print(f"  📊 Всего: {len(predictions)} предсказаний") >> analyze_project.py
echo         if len(predictions) > 0: >> analyze_project.py
echo             status_count = {} >> analyze_project.py
echo             for pred in predictions: >> analyze_project.py
echo                 status = pred.get('status', 'unknown') >> analyze_project.py
echo                 status_count[status] = status_count.get(status, 0) + 1 >> analyze_project.py
echo             print(f"\n  Статусы:") >> analyze_project.py
echo             for status, count in status_count.items(): >> analyze_project.py
echo                 pct = (count / len(predictions)) * 100 >> analyze_project.py
echo                 print(f"     {status}: {count} ({pct:.1f}%)") >> analyze_project.py
echo     except Exception as e: >> analyze_project.py
echo         print(f"  ❌ Ошибка: {e}") >> analyze_project.py
echo else: >> analyze_project.py
echo     print("  ❌ predictions.json не найден") >> analyze_project.py
echo print("\n" + "=" * 100) >> analyze_project.py
echo print("✅ АНАЛИЗ ЗАВЕРШЕН") >> analyze_project.py
echo print("=" * 100) >> analyze_project.py

python analyze_project.py