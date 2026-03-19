# check_predictor.py
"""
Проверка синтаксиса predictor.py
"""

import py_compile
import sys

def check_syntax():
    """Проверяет синтаксис файла"""
    try:
        py_compile.compile('predictor.py', doraise=True)
        print("✅ Синтаксис predictor.py в порядке!")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Ошибка синтаксиса: {e}")
        return False

if __name__ == "__main__":
    check_syntax()