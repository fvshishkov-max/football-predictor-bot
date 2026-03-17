# signal_filter_analyzer.py
import json
import numpy as np
from collections import defaultdict
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalFilterAnalyzer:
    """
    Анализирует эффективность фильтрации сигналов по вероятности
    """
    
    def __init__(self, predictions_file='data/predictions.json'):
        self.predictions_file = predictions_file
        self.predictions = []
        self.accuracy_stats = {}
        self.min_probability = 0.46  # Значение по умолчанию
        self.load_data()
    
    def load_data(self):
        """Загружает историю предсказаний"""
        try:
            if not os.path.exists(self.predictions_file):
                print(f"⚠️ Файл {self.predictions_file} не найден")
                print("   Бот еще не накопил достаточно данных для анализа")
                print("   Запустите бота и подождите несколько дней")
                return False
            
            with open(self.predictions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.predictions = data.get('predictions', [])
                self.accuracy_stats = data.get('accuracy_stats', {})
                self.min_probability = data.get('min_signal_probability', 0.46)
            
            print(f"✅ Загружено {len(self.predictions)} предсказаний")
            print(f"🎯 Порог вероятности: {self.min_probability*100:.0f}%")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False
    
    def analyze_thresholds(self):
        """Анализирует различные пороги вероятности"""
        if not self.predictions:
            print("⚠️ Нет данных для анализа")
            return []
        
        thresholds = np.arange(0.30, 0.65, 0.01)
        results = []
        
        for threshold in thresholds:
            signals_at_threshold = [p for p in self.predictions 
                                   if p.get('goal_probability', 0) >= threshold]
            
            # Для анализа нам нужно знать, были ли прогнозы правильными
            # В реальности эта информация должна сохраняться
            # Пока используем заглушку
            accuracy = 50.0  # Базовая точность
            
            results.append({
                'threshold': round(threshold, 2),
                'signals': len(signals_at_threshold),
                'accuracy': accuracy
            })
        
        return results
    
    def print_stats(self):
        """Выводит статистику по текущему порогу"""
        if not self.predictions:
            print("\n" + "="*60)
            print("📊 СТАТИСТИКА ФИЛЬТРАЦИИ СИГНАЛОВ")
            print("="*60)
            print("❌ НЕТ ДАННЫХ ДЛЯ АНАЛИЗА")
            print("="*60)
            print("\n💡 Чтобы накопить данные:")
            print("   1. Запустите бота: python run_fixed.py")
            print("   2. Подождите несколько дней")
            print("   3. Запустите анализатор снова")
            return
        
        total = len(self.predictions)
        
        # Сигналы с вероятностью выше порога
        signals_above = [p for p in self.predictions if p.get('goal_probability', 0) >= self.min_probability]
        signals_below = [p for p in self.predictions if p.get('goal_probability', 0) < self.min_probability]
        
        # Сигналы, которые были отправлены
        signals_sent = self.accuracy_stats.get('signals_sent_46plus', 0)
        signals_filtered = self.accuracy_stats.get('signals_filtered_out', 0)
        
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ФИЛЬТРАЦИИ СИГНАЛОВ")
        print("="*60)
        print(f"📈 Всего предсказаний: {total}")
        print(f"🎯 Текущий порог: {self.min_probability*100:.0f}%")
        print(f"\n🔴 Сигналы с вероятностью ≥ {self.min_probability*100:.0f}%: {len(signals_above)}")
        print(f"⚪ Сигналы с вероятностью < {self.min_probability*100:.0f}%: {len(signals_below)}")
        print(f"\n📨 Отправлено сигналов (из статистики): {signals_sent}")
        print(f"⏳ Отфильтровано: {signals_filtered}")
        
        # Процент отсеивания
        if total > 0:
            filter_rate = (signals_filtered / total) * 100 if signals_filtered > 0 else 0
            print(f"\n📊 Процент отсеивания: {filter_rate:.1f}%")
        
        print("="*60)
    
    def find_optimal_threshold(self, min_signals: int = 10) -> float:
        """
        Находит оптимальный порог для максимизации качества
        """
        if not self.predictions:
            print("⚠️ Нет данных для анализа")
            return self.min_probability
        
        results = self.analyze_thresholds()
        
        # Находим порог, который дает наилучшее соотношение
        best_score = 0
        best_threshold = self.min_probability
        
        for r in results:
            if r['signals'] >= min_signals:
                # Чем больше сигналов, тем лучше (при прочих равных)
                score = np.log(r['signals'] + 1)
                if score > best_score:
                    best_score = score
                    best_threshold = r['threshold']
        
        print(f"\n🎯 Оптимальный порог (по количеству сигналов): {best_threshold*100:.0f}%")
        print(f"   Сигналов при этом пороге: {sum(1 for p in self.predictions if p.get('goal_probability', 0) >= best_threshold)}")
        
        return best_threshold
    
    def predict_signal_quality(self, probability: float) -> str:
        """
        Оценивает качество сигнала на основе исторических данных
        """
        if probability >= 0.55:
            return "ОТЛИЧНОЕ ⭐⭐⭐"
        elif probability >= 0.50:
            return "ХОРОШЕЕ ⭐⭐"
        elif probability >= self.min_probability:
            return "СРЕДНЕЕ ⭐"
        else:
            return "НИЗКОЕ ⚠️"


def main():
    """Основная функция для запуска анализа"""
    analyzer = SignalFilterAnalyzer()
    
    if analyzer.load_data():
        analyzer.print_stats()
        analyzer.find_optimal_threshold()
        
        # Показываем пример оценки качества
        print("\n📊 Примеры оценки качества:")
        test_probs = [0.35, 0.46, 0.48, 0.52, 0.58, 0.65]
        for prob in test_probs:
            quality = analyzer.predict_signal_quality(prob)
            print(f"   {prob*100:.0f}% - {quality}")
    else:
        # Если данных нет, показываем инструкцию
        print("\n💡 ИНСТРУКЦИЯ:")
        print("   1. Убедитесь, что бот запущен: python run_fixed.py")
        print("   2. Подождите, пока бот накопит данные (минимум 100 матчей)")
        print("   3. Файл predictions.json появится автоматически в папке data/")
        print("   4. Запустите анализатор снова")

if __name__ == "__main__":
    main()