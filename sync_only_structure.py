# sync_only_structure.py
"""
Синхронизация только структуры папок data (.gitkeep)
Запуск: python sync_only_structure.py
"""

import os
import subprocess

def main():
    print("="*60)
    print("📁 СИНХРОНИЗАЦИЯ СТРУКТУРЫ DATA")
    print("="*60)
    
    # Создаем .gitkeep файлы где нужно
    print("\n1. Создание .gitkeep файлов...")
    folders = [
        'data',
        'data/predictions',
        'data/history',
        'data/stats',
        'data/logs',
        'data/backups',
        'data/models',
        'data/cache'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        gitkeep = os.path.join(folder, '.gitkeep')
        if not os.path.exists(gitkeep):
            with open(gitkeep, 'w') as f:
                f.write('')
            print(f"  ✅ {gitkeep}")
    
    # Добавляем .gitkeep файлы в Git
    print("\n2. Добавление в Git...")
    subprocess.run('git add data/**/.gitkeep', shell=True)
    subprocess.run('git add data/.gitkeep', shell=True)
    
    # Статус
    print("\n3. Статус:")
    subprocess.run('git status --short', shell=True)
    
    # Коммит
    commit = input("\n4. Введите комментарий: ").strip()
    if not commit:
        commit = "Update: Data folder structure with .gitkeep"
    
    subprocess.run(f'git commit -m "{commit}"', shell=True)
    
    # Пуш
    print("\n5. Отправка на GitHub...")
    subprocess.run('git push origin main', shell=True)
    
    print("\n✅ Готово!")

if __name__ == "__main__":
    main()