# sync_data.py
"""
Синхронизация папки data с GitHub
Запуск: python sync_data.py
"""

import os
import subprocess
import sys

def run_command(cmd):
    """Выполняет команду и выводит результат"""
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def main():
    print("="*60)
    print("📁 СИНХРОНИЗАЦИЯ ПАПКИ DATA С GITHUB")
    print("="*60)
    
    # 1. Проверяем наличие папки data
    print("\n1. Проверка локальной папки data...")
    if not os.path.exists('data'):
        print("❌ Папка data не найдена!")
        return
    
    # 2. Показываем содержимое
    print("\n2. Содержимое папки data:")
    for root, dirs, files in os.walk('data'):
        level = root.replace('data', '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        sub_indent = '  ' * (level + 1)
        for file in files:
            print(f"{sub_indent}📄 {file}")
    
    # 3. Спрашиваем, какие файлы синхронизировать
    print("\n" + "="*60)
    print("Выберите тип синхронизации:")
    print("[1] Только структуру папок (.gitkeep)")
    print("[2] Только примеры данных (без реальных данных)")
    print("[3] Все файлы (включая реальные данные)")
    print("[4] Выход")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == '4':
        print("Отмена")
        return
    
    # 4. Временно изменяем .gitignore
    print("\n3. Временное изменение .gitignore...")
    backup_gitignore = None
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            backup_gitignore = f.read()
        
        # Убираем правила для data
        lines = []
        skip_data = False
        for line in backup_gitignore.split('\n'):
            if 'data/' in line and not '!data/' in line:
                continue
            lines.append(line)
        
        with open('.gitignore.tmp', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        os.replace('.gitignore.tmp', '.gitignore')
        print("✅ .gitignore временно изменен")
    
    try:
        # 5. Добавляем файлы в зависимости от выбора
        print("\n4. Добавление файлов в Git...")
        
        if choice == '1':
            # Только .gitkeep
            for root, dirs, files in os.walk('data'):
                if '.gitkeep' in files:
                    filepath = os.path.join(root, '.gitkeep')
                    run_command(f'git add -f "{filepath}"')
        
        elif choice == '2':
            # Структура + примеры
            for root, dirs, files in os.walk('data'):
                for file in files:
                    if '.gitkeep' in file or '.example' in file:
                        filepath = os.path.join(root, file)
                        run_command(f'git add -f "{filepath}"')
        
        else:
            # Все файлы
            run_command('git add -f data/')
        
        # 6. Статус
        print("\n5. Статус добавленных файлов:")
        run_command('git status --short')
        
        # 7. Коммит
        commit_msg = input("\nВведите комментарий к коммиту: ").strip()
        if not commit_msg:
            commit_msg = "Update: Sync data folder with GitHub"
        
        print("\n6. Создание коммита...")
        run_command(f'git commit -m "{commit_msg}"')
        
        # 8. Пуш
        print("\n7. Отправка на GitHub...")
        run_command('git push origin main')
        
        print("\n✅ Синхронизация завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        # 9. Восстанавливаем .gitignore
        if backup_gitignore:
            with open('.gitignore', 'w', encoding='utf-8') as f:
                f.write(backup_gitignore)
            print("\n✅ .gitignore восстановлен")

if __name__ == "__main__":
    main()