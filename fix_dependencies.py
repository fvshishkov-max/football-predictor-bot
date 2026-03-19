# fix_dependencies.py
"""
Скрипт для исправления конфликтов зависимостей
"""

import subprocess
import sys

def fix_dependencies():
    """Исправляет конфликты зависимостей"""
    
    print("="*60)
    print("🔧 ИСПРАВЛЕНИЕ ЗАВИСИМОСТЕЙ")
    print("="*60)
    
    # Устанавливаем правильную версию h11
    print("\n📦 Устанавливаем h11==0.16.0...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "h11==0.16.0", "--force-reinstall"])
    
    # Обновляем остальные пакеты
    print("\n📦 Обновляем остальные пакеты...")
    packages = [
        "aiohttp",
        "numpy",
        "pandas",
        "scikit-learn",
        "xgboost",
        "joblib",
        "requests",
        "python-dotenv"
    ]
    
    for package in packages:
        print(f"  • {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
    
    print("\n" + "="*60)
    print("✅ Зависимости исправлены!")
    print("🚀 Запустите бота: python run_fixed.py")
    print("="*60)

if __name__ == "__main__":
    fix_dependencies()