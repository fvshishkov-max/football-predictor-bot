# performance_monitor.py
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Мониторинг производительности API запросов"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.api_times = defaultdict(lambda: deque(maxlen=window_size))
        self.api_errors = defaultdict(int)
        self.api_success = defaultdict(int)
        self.start_time = datetime.now()
        self.total_requests = 0
        self.failed_requests = 0
        
    def record_request(self, api_name: str, duration: float, success: bool = True):
        """Записывает время выполнения запроса"""
        self.api_times[api_name].append({
            'timestamp': datetime.now(),
            'duration': duration,
            'success': success
        })
        
        self.total_requests += 1
        if success:
            self.api_success[api_name] += 1
        else:
            self.api_errors[api_name] += 1
            self.failed_requests += 1
    
    def get_api_stats(self, api_name: str) -> Dict:
        """Возвращает статистику по конкретному API"""
        times = list(self.api_times[api_name])
        if not times:
            return {
                'avg_duration': 0,
                'max_duration': 0,
                'min_duration': 0,
                'success_rate': 0,
                'total_requests': 0
            }
        
        durations = [t['duration'] for t in times]
        success_count = sum(1 for t in times if t['success'])
        
        return {
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'success_rate': (success_count / len(times)) * 100,
            'total_requests': len(times),
            'errors': self.api_errors[api_name]
        }
    
    def get_all_stats(self) -> Dict:
        """Возвращает статистику по всем API"""
        stats = {}
        for api_name in set(list(self.api_times.keys()) + list(self.api_errors.keys())):
            stats[api_name] = self.get_api_stats(api_name)
        
        uptime = datetime.now() - self.start_time
        stats['system'] = {
            'uptime': str(uptime).split('.')[0],
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': ((self.total_requests - self.failed_requests) / max(1, self.total_requests)) * 100
        }
        
        return stats
    
    def get_slow_queries(self, threshold: float = 2.0) -> List[Dict]:
        """Возвращает медленные запросы (дольше threshold секунд)"""
        slow_queries = []
        for api_name, times in self.api_times.items():
            for record in times:
                if record['duration'] > threshold:
                    slow_queries.append({
                        'api': api_name,
                        'duration': record['duration'],
                        'timestamp': record['timestamp'].isoformat(),
                        'success': record['success']
                    })
        return sorted(slow_queries, key=lambda x: x['duration'], reverse=True)[:10]
    
    def generate_report(self) -> str:
        """Генерирует отчет о производительности"""
        stats = self.get_all_stats()
        slow_queries = self.get_slow_queries()
        
        report = f"📊 **ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ**\n\n"
        report += f"⏱️ Время работы: {stats['system']['uptime']}\n"
        report += f"📈 Всего запросов: {stats['system']['total_requests']}\n"
        report += f"✅ Успешно: {stats['system']['total_requests'] - stats['system']['failed_requests']}\n"
        report += f"❌ Ошибок: {stats['system']['failed_requests']}\n"
        report += f"📊 Общая успешность: {stats['system']['success_rate']:.1f}%\n\n"
        
        report += f"**ДЕТАЛЬНО ПО API:**\n"
        for api_name, api_stats in stats.items():
            if api_name != 'system':
                report += f"\n🔹 {api_name}:\n"
                report += f"   • Среднее время: {api_stats['avg_duration']:.3f}с\n"
                report += f"   • Макс время: {api_stats['max_duration']:.3f}с\n"
                report += f"   • Успешность: {api_stats['success_rate']:.1f}%\n"
                report += f"   • Запросов: {api_stats['total_requests']}\n"
        
        if slow_queries:
            report += f"\n🐌 **МЕДЛЕННЫЕ ЗАПРОСЫ (>2с):**\n"
            for q in slow_queries[:5]:
                report += f"   • {q['api']}: {q['duration']:.2f}с ({q['timestamp']})\n"
        
        return report
    
    def save_stats(self, filename: str = 'data/performance_stats.json'):
        """Сохраняет статистику в файл"""
        try:
            os.makedirs('data', exist_ok=True)
            stats = {
                'generated': datetime.now().isoformat(),
                'stats': self.get_all_stats(),
                'slow_queries': self.get_slow_queries()
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения статистики: {e}")