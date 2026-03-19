# signal_filter.py
import json
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

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
            print(f"✅ Загружено {len(self.predictions)} предсказаний")
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
                correct = sum(1 for p in signals_at_threshold 
                            if p.get('was_correct', False))
                accuracy = correct / len(signals_at_threshold) * 100
            else:
                accuracy = 0
            
            results.append({
                'threshold': threshold,
                'signals': len(signals_at_threshold),
                'accuracy': accuracy
            })
        
        return results
    
    def find_optimal_threshold(self, min_signals: int = 10) -> float:
        """
        Находит оптимальный порог для максимизации точности
        при минимальном количестве сигналов
        """
        results = self.analyze_thresholds()
        
        best_threshold = 0.46
        best_accuracy = 0
        
        for r in results:
            if r['signals'] >= min_signals and r['accuracy'] > best_accuracy:
                best_accuracy = r['accuracy']
                best_threshold = r['threshold']
        
        print(f"\n📊 Оптимальный порог: {best_threshold*100:.1f}%")
        print(f"   Сигналов: {sum(1 for p in self.predictions if p.get('goal_probability', 0) >= best_threshold)}")
        print(f"   Точность: {best_accuracy:.1f}%")
        
        return best_threshold
    
    def print_stats(self):
        """Выводит статистику по текущему порогу 46%"""
        total = len(self.predictions)
        signals_46 = [p for p in self.predictions if p.get('goal_probability', 0) >= 0.46]
        signals_below = [p for p in self.predictions if p.get('goal_probability', 0) < 0.46]
        
        correct_46 = sum(1 for p in signals_46 if p.get('was_correct', False))
        correct_below = sum(1 for p in signals_below if p.get('was_correct', False))
        
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА ФИЛЬТРАЦИИ СИГНАЛОВ")
        print("="*50)
        print(f"Всего предсказаний: {total}")
        print(f"\n🔴 Сигналы с вероятностью >= 46%: {len(signals_46)}")
        if signals_46:
            print(f"   Правильных: {correct_46}")
            print(f"   Точность: {correct_46/len(signals_46)*100:.1f}%")
        
        print(f"\n⚪ Сигналы с вероятностью < 46%: {len(signals_below)}")
        if signals_below:
            print(f"   Правильных: {correct_below}")
            print(f"   Точность: {correct_below/len(signals_below)*100:.1f}%")
        
        # Эффективность фильтрации
        if signals_46 and signals_below:
            improvement = (correct_46/len(signals_46) - correct_below/len(signals_below)) * 100
            print(f"\n📈 Улучшение точности: +{improvement:.1f}%")
    
    def plot_analysis(self):
        """Строит график зависимости точности от порога"""
        results = self.analyze_thresholds()
        
        thresholds = [r['threshold']*100 for r in results]
        accuracies = [r['accuracy'] for r in results]
        signal_counts = [r['signals'] for r in results]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # График точности
        ax1.plot(thresholds, accuracies, 'b-', linewidth=2)
        ax1.axvline(x=46, color='r', linestyle='--', label='Текущий порог 46%')
        ax1.set_xlabel('Порог вероятности (%)')
        ax1.set_ylabel('Точность (%)')
        ax1.set_title('Зависимость точности от порога вероятности')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # График количества сигналов
        ax2.plot(thresholds, signal_counts, 'g-', linewidth=2)
        ax2.axvline(x=46, color='r', linestyle='--', label='Текущий порог 46%')
        ax2.set_xlabel('Порог вероятности (%)')
        ax2.set_ylabel('Количество сигналов')
        ax2.set_title('Зависимость количества сигналов от порога')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('signal_filter_analysis.png')
        plt.show()

if __name__ == "__main__":
    analyzer = SignalFilterAnalyzer()
    analyzer.print_stats()
    analyzer.find_optimal_threshold(min_signals=20)
    # analyzer.plot_analysis()  # Раскомментировать если есть matplotlib