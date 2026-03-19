# check_stats.py
import json
import os
from datetime import datetime
import glob

def check_stats():
    """Проверяет целостность статистических данных"""
    
    print("🔍 ПРОВЕРКА СТАТИСТИКИ")
    print("="*60)
    
    # Проверяем signal_accuracy.json
    signal_accuracy_exists = os.path.exists('signal_accuracy.json')
    if signal_accuracy_exists:
        with open('signal_accuracy.json', 'r', encoding='utf-8') as f:
            stats = json.load(f)
        print(f"✅ signal_accuracy.json: {stats['stats']['total_signals']} сигналов, точность {stats['stats']['accuracy_rate']:.1f}%")
        print(f"   Правильных: {stats['stats']['correct_signals']}, Голов: {stats['stats']['goals_actual']}")
    else:
        print("❌ signal_accuracy.json не найден")
    
    # Проверяем bot_stats.json
    bot_stats_exists = os.path.exists('bot_stats.json')
    if bot_stats_exists:
        with open('bot_stats.json', 'r', encoding='utf-8') as f:
            bot_stats = json.load(f)
        print(f"✅ bot_stats.json: {bot_stats['total_signals_sent']} отправлено, {bot_stats['total_goals_confirmed']} голов")
    else:
        print("❌ bot_stats.json не найден")
    
    # Проверяем историю сигналов
    signal_files = glob.glob('signals_history_*.json')
    if signal_files:
        latest = max(signal_files)
        with open(latest, 'r', encoding='utf-8') as f:
            signals = json.load(f)
        confirmed = sum(1 for s in signals if s.get('actual_goal_minute'))
        correct = sum(1 for s in signals if s.get('was_correct') == True)
        print(f"✅ {latest}: {len(signals)} сигналов, {confirmed} подтверждено, {correct} точных")
    else:
        print("❌ Файлы истории не найдены")
    
    # Проверяем signals_history_latest.json
    if os.path.exists('signals_history_latest.json'):
        with open('signals_history_latest.json', 'r', encoding='utf-8') as f:
            latest_signals = json.load(f)
        print(f"✅ signals_history_latest.json: {len(latest_signals)} последних сигналов")
    
    # Проверяем соответствие
    if signal_accuracy_exists and bot_stats_exists:
        total_signals = stats['stats']['total_signals']
        sent_signals = bot_stats['total_signals_sent']
        
        if total_signals != sent_signals:
            print(f"⚠️ НЕСООТВЕТСТВИЕ: signal_accuracy: {total_signals}, bot_stats: {sent_signals}")
            print(f"   Разница: {total_signals - sent_signals} сигналов")
        else:
            print(f"✅ Данные согласованы")
    
    print("="*60)
    
    return {
        'signal_accuracy': stats if signal_accuracy_exists else None,
        'bot_stats': bot_stats if bot_stats_exists else None
    }

if __name__ == "__main__":
    check_stats()