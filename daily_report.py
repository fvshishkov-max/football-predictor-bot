# daily_report.py
"""
Ежедневный отчет по предсказаниям
Запуск: python daily_report.py
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict

def generate_report():
    """Генерирует отчет за день"""
    
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    # Фильтруем за последние 24 часа
    now = datetime.now()
    today_predictions = []
    
    for pred in predictions:
        ts = pred.get('timestamp', '')
        if ts:
            try:
                pred_time = datetime.fromisoformat(ts)
                if (now - pred_time).total_seconds() < 86400:  # 24 часа
                    today_predictions.append(pred)
            except:
                pass
    
    print("="*70)
    print("📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ")
    print(f"📅 {now.strftime('%Y-%m-%d')}")
    print("="*70)
    
    print(f"\n📈 Новых предсказаний за день: {len(today_predictions)}")
    print(f"📊 Всего предсказаний: {len(predictions)}")
    
    if today_predictions:
        # Распределение по периодам
        periods = {
            '0-15': 0, '15-30': 0, '30-45': 0,
            '45-60': 0, '60-75': 0, '75-90': 0, '90+': 0
        }
        
        for pred in today_predictions:
            minute = pred.get('minute', 0)
            if minute < 15:
                periods['0-15'] += 1
            elif minute < 30:
                periods['15-30'] += 1
            elif minute < 45:
                periods['30-45'] += 1
            elif minute < 60:
                periods['45-60'] += 1
            elif minute < 75:
                periods['60-75'] += 1
            elif minute < 90:
                periods['75-90'] += 1
            else:
                periods['90+'] += 1
        
        print("\n⏱ РАСПРЕДЕЛЕНИЕ ПО ПЕРИОДАМ:")
        for period, count in periods.items():
            if count > 0:
                bar = '█' * count
                print(f"  {period}: {count} прогнозов {bar}")
    
    print("\n" + "="*70)
    print("💡 РЕКОМЕНДАЦИЯ:")
    print("  • Для точного анализа нужно 100-200 предсказаний")
    print(f"  • Текущий прогресс: {len(predictions)}/100")
    print(f"  • Осталось накопить: {max(0, 100 - len(predictions))} предсказаний")
    print("="*70)

if __name__ == "__main__":
    generate_report()