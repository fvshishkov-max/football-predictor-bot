# check_data.py
"""
Проверка содержимого папки data локально и на GitHub
Запуск: python check_data.py
"""

import os
import subprocess

def main():
    print("="*60)
    print("🔍 ПРОВЕРКА ПАПКИ DATA")
    print("="*60)
    
    # Локальные файлы
    print("\n📁 ЛОКАЛЬНЫЕ ФАЙЛЫ:")
    print("-"*40)
    
    if os.path.exists('data'):
        for root, dirs, files in os.walk('data'):
            level = root.replace('data', '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            sub_indent = '  ' * (level + 1)
            for file in files:
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                if size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                print(f"{sub_indent}📄 {file} ({size_str})")
    else:
        print("❌ Папка data не найдена")
    
    # Файлы на GitHub
    print("\n🌐 ФАЙЛЫ НА GITHUB:")
    print("-"*40)
    
    try:
        result = subprocess.run(
            'git ls-tree -r main --name-only | findstr "data/"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        files = [f for f in result.stdout.strip().split('\n') if f]
        
        if files:
            for f in files:
                print(f"  📄 {f}")
            print(f"\n  Всего файлов: {len(files)}")
        else:
            print("  ❌ Нет файлов в папке data")
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()