# force_log_signals.py
"""
Добавляет логирование сигналов в predictor.py
"""

import re

def add_signal_logging():
    with open('predictor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем логирование в analyze_live_match
    if 'logger.info(f"📢 СИГНАЛ ОТПРАВЛЕН!' not in content:
        # Находим место после отправки сигнала
        pattern = r'self\.accuracy_stats\[\'signals_sent_46plus\'\] \+= 1'
        replacement = pattern + '\n                logger.info(f"📢 СИГНАЛ ОТПРАВЛЕН! Матч {match.id} ({half}) - {prediction[\'goal_probability\']*100:.1f}%")'
        content = re.sub(pattern, replacement, content)
        print("✅ Added signal logging to predictor.py")
    
    with open('predictor.py', 'w', encoding='utf-8') as f:
        f.write(content)

def add_app_logging():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем логирование в _fast_check
    if 'logger.info(f"📨 Сигнал:' not in content:
        # Находим место отправки
        pattern = r'self\.telegram_bot\.send_message\(message\)'
        replacement = pattern + '\n                            logger.info(f"📨 Сигнал отправлен в Telegram: {match.home_team.name} vs {match.away_team.name}")'
        content = re.sub(pattern, replacement, content)
        print("✅ Added send logging to app.py")
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    add_signal_logging()
    add_app_logging()
    print("\nRestart bot: python run_fixed.py")