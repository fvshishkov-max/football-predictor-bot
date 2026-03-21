# quick_stats.py
"""
Quick statistics without emojis
Запуск: python quick_stats.py
"""

import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def quick_stats():
    """Shows quick statistics"""
    
    try:
        with open('data/predictions/predictions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        predictions = data.get('predictions', [])
        stats = data.get('accuracy_stats', {})
        
        print("="*60)
        print("QUICK STATISTICS")
        print("="*60)
        
        print(f"\nTotal predictions: {len(predictions)}")
        print(f"Correct: {stats.get('correct_predictions', 0)}")
        print(f"Incorrect: {stats.get('incorrect_predictions', 0)}")
        print(f"Accuracy: {stats.get('accuracy_rate', 0)*100:.1f}%")
        
        if predictions:
            # Last 5 predictions
            print("\nLast 5 predictions:")
            for pred in predictions[-5:]:
                home = pred.get('home_team', '?')
                away = pred.get('away_team', '?')
                prob = pred.get('goal_probability', 0) * 100
                minute = pred.get('minute', 0)
                print(f"  {minute}' | {home} vs {away} | {prob:.1f}%")
        
        print("\n" + "="*60)
        print(f"Need {max(0, 100 - len(predictions))} more predictions for full analysis")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_stats()