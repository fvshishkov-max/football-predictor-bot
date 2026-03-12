# xg_monitor.py
import asyncio
import json
import os
from datetime import datetime
from collections import defaultdict
from xg_provider import XGManager

class XGMonitor:
    """Мониторинг работы xG системы"""
    
    def __init__(self, stats_file='data/xg_stats.json'):
        self.xg_manager = XGManager()
        self.stats_file = stats_file
        self.daily_stats = defaultdict(lambda: {
            'requests': 0,
            'success': 0,
            'cache_hits': 0,
            'searches': 0,
            'successful_searches': 0
        })
        
    async def monitor(self):
        """Запускает мониторинг"""
        try:
            # Загружаем статистику
            self._load_stats()
            
            while True:
                # Получаем текущую статистику
                stats = self.xg_manager.get_stats()
                
                # Обновляем дневную статистику
                today = datetime.now().strftime('%Y-%m-%d')
                self.daily_stats[today]['requests'] = stats['total_requests']
                self.daily_stats[today]['success'] = stats['successful']
                self.daily_stats[today]['cache_hits'] = stats.get('cached', 0)
                self.daily_stats[today]['searches'] = stats.get('search_requests', 0)
                self.daily_stats[today]['successful_searches'] = stats.get('successful_searches', 0)
                
                # Очищаем старые данные (старше 7 дней)
                self._clean_old_stats()
                
                # Сохраняем статистику
                self._save_stats()
                
                # Выводим в консоль
                self._print_stats(stats)
                
                await asyncio.sleep(60)  # Обновляем каждую минуту
                
        except KeyboardInterrupt:
            print("\n👋 Мониторинг остановлен")
        finally:
            await self.xg_manager.close()
    
    def _load_stats(self):
        """Загружает статистику из файла"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Загружаем дневную статистику
                    for date, stats in data.get('daily_stats', {}).items():
                        self.daily_stats[date] = stats
            except Exception as e:
                print(f"Ошибка загрузки статистики: {e}")
    
    def _save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            os.makedirs('data', exist_ok=True)
            data = {
                'daily_stats': dict(self.daily_stats),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")
    
    def _clean_old_stats(self):
        """Очищает статистику старше 7 дней"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=7)
        to_delete = []
        
        for date_str in self.daily_stats:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if date < cutoff:
                    to_delete.append(date_str)
            except:
                continue
        
        for date in to_delete:
            del self.daily_stats[date]
    
    def _print_stats(self, stats):
        """Выводит статистику в консоль"""
        print("\n" + "=" * 60)
        print(f"📊 xG МОНИТОРИНГ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        print(f"\n📈 ТЕКУЩАЯ СТАТИСТИКА:")
        print(f"   • Всего запросов: {stats['total_requests']}")
        print(f"   • Успешно: {stats['successful']} ({stats['success_rate']}%)")
        print(f"   • Из кэша: {stats.get('cached', 0)}")
        print(f"   • Поисков: {stats.get('search_requests', 0)}")
        print(f"   • Успешный поиск: {stats.get('successful_searches', 0)}")
        print(f"   •成功率 поиска: {stats.get('search_success_rate', 0)}%")
        
        print(f"\n📅 ПОСЛЕДНИЕ 7 ДНЕЙ:")
        for date, day_stats in sorted(self.daily_stats.items(), reverse=True)[:7]:
            success_rate = (day_stats['success'] / max(1, day_stats['requests'])) * 100
            search_rate = (day_stats['successful_searches'] / max(1, day_stats['searches'])) * 100
            
            print(f"\n   {date}:")
            print(f"      • Запросов: {day_stats['requests']}")
            print(f"      • Успешно: {day_stats['success']} ({success_rate:.1f}%)")
            print(f"      • Из кэша: {day_stats['cache_hits']}")
            print(f"      • Поисков: {day_stats['searches']} (успешно: {search_rate:.1f}%)")

async def main():
    monitor = XGMonitor()
    await monitor.monitor()

if __name__ == "__main__":
    asyncio.run(main())