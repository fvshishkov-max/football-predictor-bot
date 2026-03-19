# bot_analysis.py
import json
from datetime import datetime
from typing import Dict, List

class BotAnalyzer:
    """Класс для анализа работы бота"""
    
    def __init__(self, stats_file='signal_accuracy.json', signals_file='signals_history_latest.json'):
        self.stats_file = stats_file
        self.signals_file = signals_file
        self.load_data()
    
    def load_data(self):
        """Загружает данные для анализа"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        except:
            self.stats = {}
        
        try:
            with open(self.signals_file, 'r', encoding='utf-8') as f:
                self.signals = json.load(f)
        except:
            self.signals = []
    
    def analyze_accuracy(self) -> Dict:
        """Анализирует точность прогнозов"""
        stats = self.stats.get('stats', {})
        
        total = stats.get('total_signals', 0)
        correct = stats.get('correct_signals', 0)
        
        return {
            'total_signals': total,
            'correct_signals': correct,
            'accuracy_rate': stats.get('accuracy_rate', 0),
            'avg_time_error': stats.get('avg_time_error', 0),
            'goals_predicted': stats.get('goals_predicted', 0),
            'goals_actual': stats.get('goals_actual', 0)
        }
    
    def analyze_signals_by_interval(self) -> Dict:
        """Анализирует сигналы по интервалам"""
        intervals = {}
        
        for signal in self.signals:
            minute = signal.get('signal_minute', 0)
            interval = (minute // 15) * 15
            interval_key = f"{interval}-{interval+15}"
            
            if interval_key not in intervals:
                intervals[interval_key] = {'total': 0, 'correct': 0}
            
            intervals[interval_key]['total'] += 1
            if signal.get('was_correct'):
                intervals[interval_key]['correct'] += 1
        
        return intervals
    
    def generate_report(self) -> str:
        """Генерирует подробный отчет"""
        accuracy = self.analyze_accuracy()
        intervals = self.analyze_signals_by_interval()
        
        report = []
        report.append("=" * 60)
        report.append("📊 ОТЧЕТ О РАБОТЕ БОТА")
        report.append("=" * 60)
        report.append(f"📅 Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        report.append("📈 ОБЩАЯ СТАТИСТИКА:")
        report.append(f"   • Всего сигналов: {accuracy['total_signals']}")
        report.append(f"   • Правильных: {accuracy['correct_signals']}")
        report.append(f"   • Точность: {accuracy['accuracy_rate']:.1f}%")
        report.append(f"   • Средняя ошибка: {accuracy['avg_time_error']:.1f} мин")
        report.append(f"   • Всего голов: {accuracy['goals_actual']}")
        report.append("")
        report.append("⏱️ АНАЛИЗ ПО ИНТЕРВАЛАМ:")
        
        for interval, data in sorted(intervals.items()):
            accuracy_rate = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            report.append(f"   • {interval}: {data['total']} сигналов, точность {accuracy_rate:.1f}%")
        
        report.append("")
        report.append("⚙️ ПАРАМЕТРЫ МОДЕЛИ:")
        params = self.stats.get('params', {})
        report.append(f"   • Ударов на гол: {params.get('shots_per_goal', 9.5)}")
        report.append(f"   • В створ на гол: {params.get('ontarget_per_goal', 3.8)}")
        report.append(f"   • Порог сигнала: {params.get('probability_threshold', 0.5)*100}%")
        report.append("=" * 60)
        
        return '\n'.join(report)

if __name__ == "__main__":
    analyzer = BotAnalyzer()
    print(analyzer.generate_report())