# fix_analyze_method.py
"""
Исправление метода analyze_live_match в predictor.py
"""

import re

def fix_analyze():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли правильный вызов _should_send_signal
    if 'if self._should_send_signal(prediction, match):' in content:
        print("✅ Already using match parameter")
    else:
        # Заменяем вызов без match на с match
        content = content.replace(
            'if self._should_send_signal(prediction):',
            'if self._should_send_signal(prediction, match):'
        )
        print("✅ Fixed _should_send_signal call")
    
    # Убеждаемся, что возвращается signal
    pattern = r'return prediction\.get\(\'signal\'\)'
    if re.search(pattern, content):
        print("✅ Returning signal from prediction")
    else:
        print("⚠️ Returning signal may be broken")
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\nRestart bot: python run_fixed.py")

if __name__ == "__main__":
    fix_analyze()