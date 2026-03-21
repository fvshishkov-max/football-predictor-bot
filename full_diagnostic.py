# full_diagnostic.py
"""
Полная диагностика всех компонентов бота
Запуск: python full_diagnostic.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime

def check_files():
    print("="*60)
    print("1. CHECKING FILES")
    print("="*60)
    
    files = ['run_fixed.py', 'app.py', 'predictor.py', 'telegram_bot_ultimate.py', 
             'api_client.py', 'config.py', 'stats_reporter.py']
    
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            print(f"  ✅ {f} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
        else:
            print(f"  ❌ {f} NOT FOUND")

def check_predictions():
    print("\n" + "="*60)
    print("2. CHECKING PREDICTIONS")
    print("="*60)
    
    pred_file = 'data/predictions/predictions.json'
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            preds = data.get('predictions', [])
            print(f"  Total predictions: {len(preds)}")
            
            if preds:
                last = preds[-1]
                print(f"  Last: {last.get('timestamp', '')[:19]} - {last.get('home_team')} vs {last.get('away_team')}")
                print(f"  Probability: {last.get('goal_probability', 0)*100:.1f}%")
                print(f"  Minute: {last.get('minute', 0)}")
    else:
        print("  ❌ predictions.json NOT FOUND")

def check_logs():
    print("\n" + "="*60)
    print("3. CHECKING LOGS")
    print("="*60)
    
    log_file = 'data/logs/app.log'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"  Total lines: {len(lines)}")
            print("\n  Last 10 lines:")
            for line in lines[-10:]:
                print(f"    {line.strip()}")
    else:
        print("  ❌ No log file")

async def test_api():
    print("\n" + "="*60)
    print("4. TESTING API")
    print("="*60)
    
    try:
        from api_client import UnifiedFastClient
        client = UnifiedFastClient()
        
        print("  Getting live matches...")
        matches = await client.get_live_matches()
        
        print(f"  Found {len(matches)} live matches")
        
        if matches:
            print("\n  First 5 matches:")
            for m in matches[:5]:
                home = m.home_team.name if m.home_team else "?"
                away = m.away_team.name if m.away_team else "?"
                print(f"    {home} vs {away} ({m.minute or 0}') - {m.home_score or 0}:{m.away_score or 0}")
        
        await client.close()
        
    except Exception as e:
        print(f"  ERROR: {e}")

async def test_predictor():
    print("\n" + "="*60)
    print("5. TESTING PREDICTOR")
    print("="*60)
    
    try:
        from predictor import Predictor
        from models import Match, Team
        
        predictor = Predictor()
        
        # Create test match
        match = Match(
            id=99999,
            home_team=Team(id=1, name="Test Home"),
            away_team=Team(id=2, name="Test Away"),
            minute=45,
            home_score=0,
            away_score=0
        )
        
        print("  Analyzing test match...")
        result = predictor.predict_match(match)
        
        print(f"  Probability: {result.get('goal_probability', 0)*100:.1f}%")
        print(f"  Confidence: {result.get('confidence_level', 'UNKNOWN')}")
        
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("="*70)
    print("FULL DIAGNOSTIC")
    print("="*70)
    
    check_files()
    check_predictions()
    check_logs()
    
    asyncio.run(test_api())
    asyncio.run(test_predictor())
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS:")
    print("="*70)
    
    pred_file = 'data/predictions/predictions.json'
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            preds = data.get('predictions', [])
            
        if len(preds) < 10:
            print("  • Very few predictions - bot may not be generating")
        else:
            print(f"  • {len(preds)} predictions - good!")
    
    log_file = 'data/logs/app.log'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if len(lines) < 10:
                print("  • Log file has few entries - check logging")
    
    print("\n  To fix:")
    print("    1. Check if API returns matches (test_api)")
    print("    2. Check logs for errors")
    print("    3. Restart bot: python run_fixed.py")
    print("="*70)

if __name__ == "__main__":
    main()