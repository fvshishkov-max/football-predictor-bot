# fix_translation.py
"""
Исправление перевода в predictor.py
"""

import re

def fix_translation():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем английский текст на русский
    replacements = [
        ('POTENTIAL GOAL!', 'ПОТЕНЦИАЛЬНЫЙ ГОЛ!'),
        ('Score:', 'Счет:'),
        ('Minute:', 'Минута:'),
        ('Goal Probability:', 'Вероятность гола:'),
        ('Confidence:', 'Уверенность:'),
        ('1st half', '1-й тайм'),
        ('2nd half', '2-й тайм'),
        ('Extra time', 'Доп. время'),
        ('VERY HIGH', 'ОЧЕНЬ ВЫСОКАЯ'),
        ('HIGH', 'ВЫСОКАЯ'),
        ('MEDIUM', 'СРЕДНЯЯ'),
        ('LOW', 'НИЗКАЯ'),
        ('VERY LOW', 'ОЧЕНЬ НИЗКАЯ'),
        ('VERY_HIGH', 'ОЧЕНЬ ВЫСОКАЯ'),
    ]
    
    for eng, rus in replacements:
        content = content.replace(eng, rus)
    
    # Исправляем confidence_text словарь
    confidence_text_block = '''        confidence_text = {"VERY_HIGH": "ОЧЕНЬ ВЫСОКАЯ", "HIGH": "ВЫСОКАЯ", "MEDIUM": "СРЕДНЯЯ", "LOW": "НИЗКАЯ", "VERY_LOW": "ОЧЕНЬ НИЗКАЯ"}'''
    
    # Находим и заменяем старый словарь
    old_pattern = r'confidence_text = \{.*?\}'
    content = re.sub(old_pattern, confidence_text_block, content, flags=re.DOTALL)
    
    # Исправляем формат сообщения
    message_block = '''        message = f"{emoji} ⚽ ПОТЕНЦИАЛЬНЫЙ ГОЛ!\\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        message += f"🏟 {home_name}  vs  {away_name}{location_str}\\n"
        message += f"📊 Счет: {current_score}\\n"
        message += f"⏱ Минута: {match.minute or 0}' {period}\\n\\n"
        message += f"📈 Вероятность гола: {goal_prob*100:.1f}%\\n"
        message += f"🎯 Уверенность: {conf_text}"'''
    
    # Находим старый блок сообщения
    old_message_pattern = r'message = f".*?\\n"'
    content = re.sub(old_message_pattern, message_block, content, flags=re.DOTALL)
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Translation restored to Russian")
    print("\nRestart bot: python run_fixed.py")

if __name__ == "__main__":
    fix_translation()