# stats_by_date.py
"""
Статистика за определенную дату
Запуск: python stats_by_date.py 2026-03-19
"""

import sys
import json
import run_stats
from datetime import datetime

def get_stats_by_date(date_str):
    """Получает статистику за указанную дату"""
    
    # Загружаем данные
    data = run_stats.load_predictions()
    if not data:
        return None
    
    predictions = data.get('predictions', [])
    
    # Фильтруем по дате
    date_stats = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'matches': []
    }
    
    for pred in predictions:
        timestamp = pred.get('timestamp', '')
        if timestamp[:10] == date_str:
            was_correct = pred.get('was_correct', False)
            date_stats['total'] += 1
            if was_correct:
                date_stats['correct'] += 1
            else:
                date_stats['incorrect'] += 1
            
            date_stats['matches'].append({
                'home': pred.get('home_team', 'Unknown'),
                'away': pred.get('away_team', 'Unknown'),
                'prob': pred.get('goal_probability', 0) * 100,
                'correct': was_correct
            })
    
    if date_stats['total'] > 0:
        date_stats['accuracy'] = (date_stats['correct'] / date_stats['total']) * 100
    else:
        date_stats['accuracy'] = 0
    
    return date_stats

def main():
    if len(sys.argv) < 2:
        print("❌ Укажите дату в формате ГГГГ-ММ-ДД")
        print("Пример: python stats_by_date.py 2026-03-19")
        return
    
    date_str = sys.argv[1]
    
    print(f"\n📊 СТАТИСТИКА ЗА {date_str}")
    print("="*50)
    
    stats = get_stats_by_date(date_str)
    
    if not stats or stats['total'] == 0:
        print(f"❌ Нет прогнозов за {date_str}")
        return
    
    print(f"📈 Всего прогнозов: {stats['total']}")
    print(f"✅ Совпало: {stats['correct']}")
    print(f"❌ Не совпало: {stats['incorrect']}")
    print(f"🎯 Точность: {stats['accuracy']:.1f}%")
    
    if stats['matches']:
        print("\n📋 Матчи:")
        for match in stats['matches']:
            mark = "✅" if match['correct'] else "❌"
            print(f"  {mark} {match['home']} vs {match['away']} - {match['prob']:.1f}%")
    
    # Спрашиваем, отправить ли в Telegram
    send = input("\n📨 Отправить в Telegram? (y/n): ").lower()
    if send == 'y':
        lines = [
            f"📊 **СТАТИСТИКА ЗА {date_str}**",
            "━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"📈 Прогнозов: {stats['total']}",
            f"✅ Совпало: {stats['correct']}",
            f"❌ Не совпало: {stats['incorrect']}",
            f"🎯 Точность: {stats['accuracy']:.1f}%"
        ]
        
        if stats['matches']:
            lines.extend(["", "📋 Матчи:"])
            for match in stats['matches'][-5:]:  # Последние 5
                mark = "✅" if match['correct'] else "❌"
                lines.append(f"  {mark} {match['home']} vs {match['away']} - {match['prob']:.1f}%")
        
        message = "\n".join(lines)
        run_stats.send_telegram_message(message)

if __name__ == "__main__":
    main()