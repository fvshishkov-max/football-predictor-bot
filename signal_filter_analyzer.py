# signal_filter_analyzer.py
import json
import numpy as np
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalFilterAnalyzer:
    """
    Анализирует эффективность фильтрации сигналов по вероятности
    """
    
    def __init__(self, predictions_file='data/predictions.json'):
        self.predictions_file = predictions_file
        self.predictions = []
        self.load_data()
    
    def load_data(self):
        """Загружает историю предсказаний"""
        try:
            with open(self.predictions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.predictions = data.get('predictions', [])
                self.accuracy_stats = data.get('accuracy_stats', {})
                self.min_probability = data.get('min_signal_probability', 0.46)
            print(f"✅ Загружено {len(self.predictions)} предсказаний")
            print(f"🎯 Порог вероятности: {self.min_probability*100:.0f}%")
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
    
    def analyze_thresholds(self):
        """Анализирует различные пороги вероятности"""
        thresholds = np.arange(0.30, 0.65, 0.01)
        results = []
        
        for threshold in thresholds:
            signals_at_threshold = [p for p in self.predictions 
                                   if p.get('goal_probability', 0) >= threshold]
            
            if signals_at_threshold:
                # Для анализа нам нужно знать, были ли прогнозы правильными
                # Это требует дополнительных данных, которых может не быть
                correct = 0
                for p in signals_at_threshold:
                    if p.get('was_correct') is not None:
                        if p.get('was_correct'):
                            correct += 1
                
                accuracy = correct / len(signals_at_threshold) * 100 if correct > 0 else 0
            else:
                accuracy = 0
            
            results.append({
                'threshold': threshold,
                'signals': len(signals_at_threshold),
                'accuracy': accuracy
            })
        
        return results
    
    def print_stats(self):
        """Выводит статистику по текущему порогу"""
        total = len(self.predictions)
        
        # Сигналы с вероятностью выше порога
        signals_above = [p for p in self.predictions if p.get('goal_probability', 0) >= self.min_probability]
        signals_below = [p for p in self.predictions if p.get('goal_probability', 0) < self.min_probability]
        
        # Сигналы, которые были отправлены (если есть информация)
        signals_sent = [p for p in self.predictions if p.get('signal')]
        
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ФИЛЬТРАЦИИ СИГНАЛОВ")
        print("="*60)
        print(f"Всего предсказаний: {total}")
        print(f"Текущий порог: {self.min_probability*100:.0f}%")
        print(f"\n🔴 Сигналы с вероятностью >= {self.min_probability*100:.0f}%: {len(signals_above)}")
        print(f"⚪ Сигналы с вероятностью < {self.min_probability*100:.0f}%: {len(signals_below)}")
        print(f"📨 Отправлено сигналов (из статистики): {self.accuracy_stats.get('signals_sent_46plus', 0)}")
        print(f"⏳ Отфильтровано: {self.accuracy_stats.get('signals_filtered_out', 0)}")
        
        # Процент отсеивания
        if total > 0:
            filter_rate = len(signals_below) / total * 100
            print(f"\n📊 Процент отсеивания: {filter_rate:.1f}%")
        
        print("="*60)
    
    def find_optimal_threshold(self, min_signals: int = 10) -> float:
        """
        Находит оптимальный порог для максимизации качества
        """
        results = self.analyze_thresholds()
        
        # Находим порог, который дает наилучшее соотношение
        best_score = 0
        best_threshold = self.min_probability
        
        for r in results:
            if r['signals'] >= min_signals:
                # Чем выше точность и больше сигналов, тем лучше
                score = r['accuracy'] * np.log(r['signals'] + 1)
                if score > best_score:
                    best_score = score
                    best_threshold = r['threshold']
        
        print(f"\n🎯 Оптимальный порог: {best_threshold*100:.1f}%")
        return best_threshold

if __name__ == "__main__":
    analyzer = SignalFilterAnalyzer()
    analyzer.print_stats()
    analyzer.find_optimal_threshold()