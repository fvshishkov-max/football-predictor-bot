# check_signals.py
"""
Проверка, какие предсказания должны были отправиться в Telegram
"""

import json

def check_signals():
    with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = data.get('predictions', [])
    
    print("="*70)
    print("SIGNALS CHECK (probability > 46%)")
    print("="*70)
    
    signals = [p for p in predictions if p.get('goal_probability', 0) > 0.46]
    
    print(f"\nTotal predictions: {len(predictions)}")
    print(f"Signals to send: {len(signals)}")
    
    if signals:
        print("\nSignals that should have been sent:")
        for pred in signals[-10:]:
            ts = pred.get('timestamp', '')[:16]
            home = pred.get('home_team', '?')
            away = pred.get('away_team', '?')
            prob = pred.get('goal_probability', 0) * 100
            minute = pred.get('minute', 0)
            print(f"  {ts} | {minute:2d}' | {home} vs {away} | {prob:.1f}%")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    check_signals()