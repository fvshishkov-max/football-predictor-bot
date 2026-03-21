# force_check_matches.py
"""
Принудительная проверка матчей в обход цикла
Запуск: python force_check_matches.py
"""

import asyncio
import sys
from datetime import datetime

async def force_check():
    print("="*60)
    print("FORCE CHECKING MATCHES")
    print("="*60)
    
    try:
        from api_client import UnifiedFastClient
        from predictor import Predictor
        from models import Match
        
        print("\n1. Initializing API client...")
        client = UnifiedFastClient()
        
        print("\n2. Getting live matches...")
        matches = await client.get_live_matches()
        
        print(f"\n3. Found {len(matches)} live matches")
        
        if matches:
            print("\nFirst 5 matches:")
            for match in matches[:5]:
                home = match.home_team.name if match.home_team else "?"
                away = match.away_team.name if match.away_team else "?"
                minute = match.minute or 0
                score = f"{match.home_score or 0}:{match.away_score or 0}"
                print(f"  {home} vs {away} ({minute}') - {score}")
        
        await client.close()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_check())