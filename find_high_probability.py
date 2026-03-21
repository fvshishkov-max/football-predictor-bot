# find_high_probability.py
"""
Поиск матчей с высокой вероятностью гола
"""

import json
import asyncio
from api_client import UnifiedFastClient
from predictor import Predictor

async def find_high_prob():
    print("="*60)
    print("SEARCHING FOR HIGH PROBABILITY MATCHES")
    print("="*60)
    
    client = UnifiedFastClient()
    predictor = Predictor()
    
    print("\n1. Getting live matches...")
    matches = await client.get_live_matches()
    print(f"   Found {len(matches)} matches")
    
    print("\n2. Analyzing matches...")
    print("-"*40)
    
    high_prob = []
    
    for match in matches[:20]:  # Проверяем первые 20
        home = match.home_team.name if match.home_team else "?"
        away = match.away_team.name if match.away_team else "?"
        minute = match.minute or 0
        
        prediction = predictor.predict_match(match)
        prob = prediction.get('goal_probability', 0) * 100
        conf = prediction.get('confidence_level', 'UNKNOWN')
        
        if prob > 46:
            high_prob.append((home, away, minute, prob, conf))
            print(f"  🔴 {home} vs {away} ({minute}') - {prob:.1f}% ({conf})")
        elif prob > 40:
            print(f"  🟡 {home} vs {away} ({minute}') - {prob:.1f}% ({conf})")
        else:
            print(f"  ⚪ {home} vs {away} ({minute}') - {prob:.1f}% ({conf})")
    
    print("\n" + "="*60)
    print(f"SUMMARY: Found {len(high_prob)} matches with >46% probability")
    
    if high_prob:
        print("\nThese matches should trigger signals:")
        for h, a, m, p, c in high_prob:
            print(f"  {h} vs {a} ({m}') - {p:.1f}% ({c})")
    else:
        print("\n⚠️ No matches with >46% probability found!")
        print("   Check if predictor is working correctly")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(find_high_prob())