# real_time_analyzer.py
import json
import time
import os
from datetime import datetime
from typing import Dict, List
import matplotlib.pyplot as plt
from collections import Counter

class RealTimeAnalyzer:
    """Анализатор работы бота в реальном времени"""
    
    def __init__(self):
        self.stats_file = 'signal_accuracy.json'
        self.signals_dir = 'signals'
        self.log_file = 'football_bot.log'
        self.load_data()
    
    def load_data(self):
        """Загружает текущие данные"""
        # Загружаем статистику
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        except:
            self.stats = {'stats': {}, 'params': {}}
        
        # Загружаем последнюю историю сигналов
        self.signals = []
        signal_files = [f for f in os.listdir('.') if f.startswith('signals_history_') and f.endswith('.json')]
        if signal_files:
            latest = max(signal_files)
            try:
                with open(latest, 'r', encoding='utf-8') as f:
                    self.signals = json.load(f)
            except:
                pass
    
    def get_current_stats(self) -> Dict:
        """Возвращает текущую статистику"""
        stats_data = self.stats.get('stats', {})
        return {
            'total_signals': stats_data.get('total_signals', 0),
            'correct_signals': stats_data.get('correct_signals', 0),
            'accuracy_rate': stats_data.get('accuracy_rate', 0),
            'goals_actual': stats_data.get('goals_actual', 0),
            'avg_time_error': stats_data.get('avg_time_error', 0)
        }
    
    def analyze_signals_by_time(self) -> Dict:
        """Анализирует сигналы по времени матча"""
        intervals = {f"{i}-{i+15}": 0 for i in range(0, 90, 15)}
        
        for signal in self.signals:
            minute = signal.get('signal_minute', 0)
            interval = f"{(minute // 15) * 15}-{((minute // 15) * 15) + 15}"
            if interval in intervals:
                intervals[interval] += 1
        
        return intervals
    
    def print_report(self):
        """Выводит отчет в консоль"""
        stats = self.get_current_stats()
        time_analysis = self.analyze_signals_by_time()
        
        print("\n" + "="*60)
        print("📊 ОТЧЕТ О РАБОТЕ БОТА")
        print("="*60)
        print(f"📅 Время анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   • Всего сигналов: {stats['total_signals']}")
        print(f"   • Точных сигналов: {stats['correct_signals']}")
        print(f"   • Точность: {stats['accuracy_rate']:.1f}%")
        print(f"   • Всего голов: {stats['goals_actual']}")
        print(f"   • Средняя ошибка: {stats['avg_time_error']:.1f} мин")
        
        print("\n⏱️ РАСПРЕДЕЛЕНИЕ СИГНАЛОВ ПО ВРЕМЕНИ:")
        for interval, count in time_analysis.items():
            if count > 0:
                percentage = (count / stats['total_signals'] * 100) if stats['total_signals'] > 0 else 0
                bar = "█" * int(percentage / 5)
                print(f"   • {interval}: {count} сигналов {bar} {percentage:.1f}%")
        
        print("\n⚙️ ПАРАМЕТРЫ МОДЕЛИ:")
        params = self.stats.get('params', {})
        print(f"   • Ударов на гол: {params.get('shots_per_goal', 9.5)}")
        print(f"   • В створ на гол: {params.get('ontarget_per_goal', 3.8)}")
        print(f"   • Порог вероятности: {params.get('probability_threshold', 0.5)*100}%")
        print("="*60)
    
    def watch_logs(self, lines=10):
        """Показывает последние строки лога"""
        print(f"\n📋 ПОСЛЕДНИЕ {lines} СТРОК ЛОГА:")
        print("-"*40)
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()[-lines:]
                for line in log_lines:
                    print(line.strip())
        except:
            print("❌ Не удалось прочитать лог-файл")
        print("-"*40)
    
    def monitor(self, interval=5):
        """Мониторинг в реальном времени"""
        try:
            while True:
                self.load_data()
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_report()
                self.watch_logs(5)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Мониторинг остановлен")

if __name__ == "__main__":
    analyzer = RealTimeAnalyzer()
    
    print("🔍 Режимы работы:")
    print("1. Разовый отчет")
    print("2. Непрерывный мониторинг (обновление каждые 5 сек)")
    print("3. Анализ сигналов")
    
    choice = input("\nВыберите режим (1-3): ").strip()
    
    if choice == '1':
        analyzer.load_data()
        analyzer.print_report()
        analyzer.watch_logs(20)
    
    elif choice == '2':
        analyzer.monitor()
    
    elif choice == '3':
        analyzer.load_data()
        print("\n📊 ДЕТАЛЬНЫЙ АНАЛИЗ СИГНАЛОВ:")
        time_analysis = analyzer.analyze_signals_by_time()
        for interval, count in time_analysis.items():
            if count > 0:
                print(f"   {interval}: {count} сигналов")