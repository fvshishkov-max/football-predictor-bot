# live_match_monitor.py
"""
Мониторинг live матчей с подходящими параметрами для сигналов
Запуск: python live_match_monitor.py
"""

import asyncio
import time
from datetime import datetime
from api_client import UnifiedFastClient
from predictor import Predictor
import config

class LiveMatchMonitor:
    def __init__(self):
        self.client = UnifiedFastClient()
        self.predictor = Predictor()
        self.checked_matches = set()
        
    async def check_match(self, match):
        """Проверяет один матч"""
        home = match.home_team.name if match.home_team else "?"
        away = match.away_team.name if match.away_team else "?"
        minute = match.minute or 0
        score = f"{match.home_score or 0}:{match.away_score or 0}"
        
        # Получаем статистику
        stats = await self.client.get_match_statistics(match)
        if stats:
            match.stats = stats
            
            # Анализируем матч
            prediction = self.predictor.predict_match(match)
            prob = prediction.get('goal_probability', 0) * 100
            conf = prediction.get('confidence_level', 'UNKNOWN')
            signal = prediction.get('signal')
            
            # Получаем статистику
            xg_home = stats.get('xg_home', 0.5)
            xg_away = stats.get('xg_away', 0.5)
            shots_home = stats.get('shots_home', 0)
            shots_away = stats.get('shots_away', 0)
            shots_ontarget_home = stats.get('shots_ontarget_home', 0)
            shots_ontarget_away = stats.get('shots_ontarget_away', 0)
            possession_home = stats.get('possession_home', 50)
            possession_away = stats.get('possession_away', 50)
            corners_home = stats.get('corners_home', 0)
            corners_away = stats.get('corners_away', 0)
            
            # Проверяем, есть ли статистика
            has_stats = (shots_home > 0 or shots_away > 0 or 
                        shots_ontarget_home > 0 or shots_ontarget_away > 0 or
                        xg_home != 0.5 or xg_away != 0.5)
            
            return {
                'id': match.id,
                'home': home,
                'away': away,
                'minute': minute,
                'score': score,
                'prob': prob,
                'confidence': conf,
                'signal': signal is not None,
                'stats': {
                    'shots': (shots_home, shots_away),
                    'shots_ontarget': (shots_ontarget_home, shots_ontarget_away),
                    'xg': (xg_home, xg_away),
                    'possession': (possession_home, possession_away),
                    'corners': (corners_home, corners_away),
                    'has_stats': has_stats
                }
            }
        return None
    
    async def monitor(self):
        """Мониторинг live матчей"""
        print("="*80)
        print("🔍 МОНИТОРИНГ LIVE МАТЧЕЙ")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        while True:
            try:
                # Получаем live матчи
                matches = await self.client.get_live_matches()
                
                if not matches:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Нет live матчей")
                    await asyncio.sleep(30)
                    continue
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Проверка {len(matches)} матчей...")
                print("-"*80)
                
                # Проверяем каждый матч
                for match in matches:
                    result = await self.check_match(match)
                    if not result:
                        continue
                    
                    # Определяем статус
                    if result['signal']:
                        status = "🔴 СИГНАЛ"
                    elif result['prob'] >= 46:
                        status = "🟡 ВЫСОКАЯ ВЕРОЯТНОСТЬ"
                    else:
                        status = "⚪ НИЗКАЯ"
                    
                    # Форматируем статистику
                    stats = result['stats']
                    stats_str = ""
                    if stats['has_stats']:
                        stats_parts = []
                        if stats['shots'][0] > 0 or stats['shots'][1] > 0:
                            stats_parts.append(f"У:{stats['shots'][0]}:{stats['shots'][1]}")
                        if stats['shots_ontarget'][0] > 0 or stats['shots_ontarget'][1] > 0:
                            stats_parts.append(f"ВС:{stats['shots_ontarget'][0]}:{stats['shots_ontarget'][1]}")
                        if stats['xg'][0] != 0.5 or stats['xg'][1] != 0.5:
                            stats_parts.append(f"xG:{stats['xg'][0]:.2f}:{stats['xg'][1]:.2f}")
                        if stats['possession'][0] != 50 or stats['possession'][1] != 50:
                            stats_parts.append(f"Вл:{stats['possession'][0]:.0f}:{stats['possession'][1]:.0f}")
                        if stats['corners'][0] > 0 or stats['corners'][1] > 0:
                            stats_parts.append(f"Уг:{stats['corners'][0]}:{stats['corners'][1]}")
                        stats_str = f" | {' | '.join(stats_parts)}"
                    
                    print(f"{status} | {result['minute']:2d}' | {result['score']} | {result['home']:25} vs {result['away']:25} | {result['prob']:5.1f}% | {result['confidence']:10} {stats_str}")
                    
                    # Если сигнал, показываем подробнее
                    if result['signal']:
                        print(f"   → СИГНАЛ БУДЕТ ОТПРАВЛЕН!")
                
                print("-"*80)
                print(f"Следующая проверка через 30 секунд...")
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                await asyncio.sleep(10)
    
    async def close(self):
        await self.client.close()

async def main():
    monitor = LiveMatchMonitor()
    try:
        await monitor.monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Мониторинг остановлен")
        await monitor.close()

if __name__ == "__main__":
    asyncio.run(main())