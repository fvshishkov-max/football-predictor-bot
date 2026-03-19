# real_time_analyzer_simple.py
import json
import time
import os
from datetime import datetime
from typing import Dict, List
import glob

class RealTimeAnalyzer:
    """Анализатор работы бота в реальном времени (упрощенная версия)"""
    
    def __init__(self):
        self.stats_file = 'signal_accuracy.json'
        self.log_file = 'football_bot.log'
        self.load_data()
    
    def load_data(self):
        """Загружает текущие данные"""
        # Загружаем статистику
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {'stats': {}, 'params': {}}
                print(f"⚠️ Файл {self.stats_file} не найден, создаем новый")
                self.save_stats()
        except Exception as e:
            print(f"❌ Ошибка загрузки статистики: {e}")
            self.stats = {'stats': {}, 'params': {}}
        
        # Загружаем последнюю историю сигналов
        self.signals = []
        signal_files = glob.glob('signals_history_*.json')
        if signal_files:
            latest = max(signal_files)
            try:
                with open(latest, 'r', encoding='utf-8') as f:
                    self.signals = json.load(f)
                print(f"✅ Загружено {len(self.signals)} сигналов из {latest}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {latest}: {e}")
    
    def save_stats(self):
        """Сохраняет статистику"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения статистики: {e}")
    
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
    
    def analyze_signal_accuracy(self) -> Dict:
        """Анализирует точность сигналов"""
        correct = 0
        total = 0
        time_errors = []
        
        for signal in self.signals:
            if signal.get('was_correct') is not None:
                total += 1
                if signal['was_correct']:
                    correct += 1
                if signal.get('time_error'):
                    time_errors.append(signal['time_error'])
        
        return {
            'total_confirmed': total,
            'correct_confirmed': correct,
            'accuracy_confirmed': (correct / total * 100) if total > 0 else 0,
            'avg_error': sum(time_errors) / len(time_errors) if time_errors else 0
        }
    
    def print_report(self):
        """Выводит отчет в консоль"""
        stats = self.get_current_stats()
        time_analysis = self.analyze_signals_by_time()
        signal_accuracy = self.analyze_signal_accuracy()
        
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
        
        if signal_accuracy['total_confirmed'] > 0:
            print("\n✅ ПОДТВЕРЖДЕННЫЕ СИГНАЛЫ:")
            print(f"   • Подтверждено: {signal_accuracy['total_confirmed']}")
            print(f"   • Точных: {signal_accuracy['correct_confirmed']}")
            print(f"   • Точность: {signal_accuracy['accuracy_confirmed']:.1f}%")
            print(f"   • Средняя ошибка: {signal_accuracy['avg_error']:.1f} мин")
        
        print("\n⏱️ РАСПРЕДЕЛЕНИЕ СИГНАЛОВ ПО ВРЕМЕНИ:")
        total_signals = stats['total_signals']
        if total_signals > 0:
            for interval, count in time_analysis.items():
                if count > 0:
                    percentage = (count / total_signals * 100)
                    bar = "█" * int(percentage / 5)
                    print(f"   • {interval}: {count} сигналов {bar} {percentage:.1f}%")
        else:
            print("   • Нет данных")
        
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
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()[-lines:]
                    for line in log_lines:
                        print(line.strip())
            else:
                print("❌ Лог-файл не найден")
        except Exception as e:
            print(f"❌ Ошибка чтения лога: {e}")
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
    print("3. Детальный анализ сигналов")
    
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
        signal_accuracy = analyzer.analyze_signal_accuracy()
        
        print("\n⏱️ ПО ИНТЕРВАЛАМ:")
        for interval, count in time_analysis.items():
            if count > 0:
                print(f"   {interval}: {count} сигналов")
        
        print("\n✅ ПО ТОЧНОСТИ:")
        print(f"   Подтверждено сигналов: {signal_accuracy['total_confirmed']}")
        print(f"   Точность: {signal_accuracy['accuracy_confirmed']:.1f}%")
        if signal_accuracy['total_confirmed'] > 0:
            print(f"   Средняя ошибка: {signal_accuracy['avg_error']:.1f} мин")