# analyze_current_data.py
"""
Анализ текущих предсказаний
Запуск: python analyze_current_data.py
"""

import json
from collections import defaultdict
from datetime import datetime

def analyze():
    """Анализирует текущие данные"""
    
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        
        print("="*70)
        print("⏱ АНАЛИЗ ТЕКУЩИХ ПРЕДСКАЗАНИЙ")
        print("="*70)
        
        if len(predictions) < 10:
            print(f"\n⚠️ Мало данных для анализа ({len(predictions)} предсказаний)")
            print("   Нужно минимум 50-100 предсказаний для статистически значимых выводов")
            print("   Продолжайте работу бота и проверьте через несколько дней\n")
            view_predictions()
            return
        
        # Статистика по минутам
        minute_dist = defaultdict(int)
        for pred in predictions:
            minute = pred.get('minute', 0)
            minute_dist[minute] += 1
        
        # Периоды
        periods = {
            '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
            '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
            '90+': (90, 120)
        }
        
        period_counts = defaultdict(int)
        for minute, count in minute_dist.items():
            for period, (start, end) in periods.items():
                if start <= minute < end:
                    period_counts[period] += count
                    break
        
        total = sum(period_counts.values())
        
        print(f"\n📊 Распределение предсказаний по периодам (всего: {total}):")
        print("-"*50)
        
        for period in periods.keys():
            count = period_counts.get(period, 0)
            percent = (count / total * 100) if total > 0 else 0
            bar = '█' * int(percent / 2)
            print(f"  {period}: {count:4d} предсказаний ({percent:5.1f}%) {bar}")
        
        # Последние предсказания
        print("\n📋 ПОСЛЕДНИЕ 5 ПРЕДСКАЗАНИЙ:")
        print("-"*50)
        
        for pred in predictions[-5:]:
            ts = pred.get('timestamp', '')[:16]
            home = pred.get('home_team', '?')
            away = pred.get('away_team', '?')
            prob = pred.get('goal_probability', 0) * 100
            minute = pred.get('minute', 0)
            print(f"  {ts} | {minute}' | {home} vs {away} | {prob:.1f}%")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\nЗапустите: python view_predictions.py")

if __name__ == "__main__":
    analyze()