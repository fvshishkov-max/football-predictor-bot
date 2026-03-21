# analyze_system_performance.py
"""
Глубокий анализ работы системы: отбор матчей, самоанализ, самообучение
Запуск: python analyze_system_performance.py
"""

import json
import os
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
from pathlib import Path

class SystemAnalyzer:
    def __init__(self):
        self.predictions_file = 'data/predictions/predictions.json'
        self.stats_file = 'data/stats/prediction_stats.json'
        self.predictions = []
        self.stats = {}
        self.load_data()
    
    def load_data(self):
        """Загружает данные о предсказаниях"""
        if os.path.exists(self.predictions_file):
            with open(self.predictions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.predictions = data.get('predictions', [])
                self.stats = data.get('accuracy_stats', {})
            print(f"✅ Загружено {len(self.predictions)} предсказаний")
        else:
            print("❌ Нет данных о предсказаниях")
    
    def analyze_match_selection(self):
        """Анализирует отбор матчей"""
        print("\n" + "="*70)
        print("📊 АНАЛИЗ ОТБОРА МАТЧЕЙ")
        print("="*70)
        
        if not self.predictions:
            print("❌ Нет данных для анализа")
            return
        
        # Распределение по минутам
        minute_dist = defaultdict(int)
        for pred in self.predictions:
            minute = pred.get('minute', 0)
            minute_dist[minute] += 1
        
        # Периоды
        periods = {
            '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
            '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
            '90+': (90, 120)
        }
        
        period_dist = defaultdict(int)
        for minute, count in minute_dist.items():
            for period, (start, end) in periods.items():
                if start <= minute < end:
                    period_dist[period] += count
                    break
        
        print("\n📈 РАСПРЕДЕЛЕНИЕ ПРОГНОЗОВ ПО ПЕРИОДАМ:")
        print("-"*50)
        total = sum(period_dist.values())
        for period in periods.keys():
            count = period_dist.get(period, 0)
            percent = (count / total * 100) if total > 0 else 0
            bar = '█' * int(percent / 2)
            print(f"  {period}: {count:5d} прогнозов ({percent:5.1f}%) {bar}")
        
        return period_dist
    
    def analyze_accuracy_by_confidence(self):
        """Анализирует точность по уровням уверенности"""
        print("\n" + "="*70)
        print("🎯 АНАЛИЗ ТОЧНОСТИ ПО УРОВНЯМ УВЕРЕННОСТИ")
        print("="*70)
        
        conf_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for pred in self.predictions:
            conf = pred.get('confidence_level', 'UNKNOWN')
            was_correct = pred.get('was_correct', False)
            conf_stats[conf]['total'] += 1
            if was_correct:
                conf_stats[conf]['correct'] += 1
        
        print("\n📊 ТОЧНОСТЬ ПО УРОВНЯМ:")
        print("-"*50)
        for conf in ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']:
            if conf in conf_stats:
                total = conf_stats[conf]['total']
                correct = conf_stats[conf]['correct']
                acc = (correct / total * 100) if total > 0 else 0
                bar = '█' * int(acc / 2)
                print(f"  {conf}: {total:5d} прогнозов, точность {acc:5.1f}% {bar}")
        
        return conf_stats
    
    def analyze_accuracy_by_minute(self):
        """Анализирует точность по минутам"""
        print("\n" + "="*70)
        print("⏱ АНАЛИЗ ТОЧНОСТИ ПО МИНУТАМ")
        print("="*70)
        
        minute_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for pred in self.predictions:
            minute = pred.get('minute', 0)
            was_correct = pred.get('was_correct', False)
            minute_stats[minute]['total'] += 1
            if was_correct:
                minute_stats[minute]['correct'] += 1
        
        # Периоды
        periods = {
            '0-15': (0, 15), '15-30': (15, 30), '30-45': (30, 45),
            '45-60': (45, 60), '60-75': (60, 75), '75-90': (75, 90),
            '90+': (90, 120)
        }
        
        print("\n📊 ТОЧНОСТЬ ПО ПЕРИОДАМ:")
        print("-"*50)
        for period, (start, end) in periods.items():
            total = 0
            correct = 0
            for minute in range(start, end):
                total += minute_stats[minute]['total']
                correct += minute_stats[minute]['correct']
            acc = (correct / total * 100) if total > 0 else 0
            bar = '█' * int(acc / 2)
            print(f"  {period}: {total:5d} прогнозов, точность {acc:5.1f}% {bar}")
        
        return minute_stats
    
    def analyze_self_learning(self):
        """Анализирует эффективность самообучения"""
        print("\n" + "="*70)
        print("🧠 АНАЛИЗ САМООБУЧЕНИЯ")
        print("="*70)
        
        if not self.predictions:
            print("❌ Нет данных для анализа")
            return
        
        # Сортируем по времени
        predictions_sorted = sorted(self.predictions, 
                                   key=lambda x: x.get('timestamp', ''))
        
        # Разбиваем на периоды
        period_size = max(10, len(predictions_sorted) // 10)
        periods = []
        
        for i in range(0, len(predictions_sorted), period_size):
            period_predictions = predictions_sorted[i:i+period_size]
            if period_predictions:
                correct = sum(1 for p in period_predictions if p.get('was_correct', False))
                total = len(period_predictions)
                acc = (correct / total * 100) if total > 0 else 0
                periods.append({
                    'start': i,
                    'end': i + total,
                    'total': total,
                    'correct': correct,
                    'accuracy': acc
                })
        
        print("\n📈 ДИНАМИКА ТОЧНОСТИ (по периодам):")
        print("-"*50)
        for i, period in enumerate(periods):
            bar = '█' * int(period['accuracy'] / 2)
            print(f"  Период {i+1:2d} (прогнозы {period['start']}-{period['end']}): "
                  f"{period['accuracy']:5.1f}% {bar}")
        
        # Тренд
        if len(periods) >= 2:
            first_acc = periods[0]['accuracy']
            last_acc = periods[-1]['accuracy']
            trend = last_acc - first_acc
            if trend > 0:
                print(f"\n✅ ПОЛОЖИТЕЛЬНЫЙ ТРЕНД: +{trend:.1f}% (было {first_acc:.1f}%, стало {last_acc:.1f}%)")
            elif trend < 0:
                print(f"\n⚠️ ОТРИЦАТЕЛЬНЫЙ ТРЕНД: {trend:.1f}% (было {first_acc:.1f}%, стало {last_acc:.1f}%)")
            else:
                print(f"\n➡️ ТРЕНД СТАБИЛЕН: {first_acc:.1f}% -> {last_acc:.1f}%")
        
        return periods
    
    def analyze_feature_importance(self):
        """Анализирует важность признаков"""
        print("\n" + "="*70)
        print("📊 АНАЛИЗ ВАЖНОСТИ ПРИЗНАКОВ")
        print("="*70)
        
        feature_importance = self.stats.get('feature_importance', {})
        
        if feature_importance:
            print("\n🔝 ТОП-10 ВАЖНЫХ ПРИЗНАКОВ:")
            print("-"*50)
            sorted_features = sorted(feature_importance.items(), 
                                     key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in sorted_features:
                bar = '█' * int(importance * 50)
                print(f"  {feature}: {importance:.4f} {bar}")
        else:
            print("❌ Нет данных о важности признаков (XGBoost не обучен)")
    
    def generate_recommendations(self):
        """Генерирует рекомендации по улучшению"""
        print("\n" + "="*70)
        print("💡 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ")
        print("="*70)
        
        recommendations = []
        
        # Анализ точности
        total = self.stats.get('total_predictions', 0)
        correct = self.stats.get('correct_predictions', 0)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        if accuracy < 50:
            recommendations.append("🔴 Критически низкая точность (<50%)")
            recommendations.append("   • Увеличить порог вероятности до 52-55%")
            recommendations.append("   • Добавить больше факторов в анализ")
            recommendations.append("   • Проверить качество входных данных")
        elif accuracy < 60:
            recommendations.append("🟡 Средняя точность (50-60%)")
            recommendations.append("   • Можно улучшить настройкой порогов")
            recommendations.append("   • Добавить фильтрацию по лигам")
        else:
            recommendations.append("🟢 Хорошая точность (>60%)")
            recommendations.append("   • Продолжать накопление данных")
            recommendations.append("   • Оптимизировать время отправки")
        
        # Анализ данных
        if len(self.predictions) < 100:
            recommendations.append(f"\n⚠️ Мало данных для обучения ({len(self.predictions)} предсказаний)")
            recommendations.append("   • Нужно минимум 100-200 предсказаний для стабильного обучения")
        
        # Анализ XGBoost
        if not self.stats.get('feature_importance'):
            recommendations.append("\n⚠️ XGBoost не обучен")
            recommendations.append("   • Накопите 100+ предсказаний для обучения модели")
        
        for rec in recommendations:
            print(rec)
    
    def run_full_analysis(self):
        """Запускает полный анализ"""
        print("="*80)
        print("🔍 ПОЛНЫЙ АНАЛИЗ СИСТЕМЫ")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"  • Всего предсказаний: {len(self.predictions)}")
        print(f"  • Правильных: {self.stats.get('correct_predictions', 0)}")
        print(f"  • Неправильных: {self.stats.get('incorrect_predictions', 0)}")
        print(f"  • Общая точность: {self.stats.get('accuracy_rate', 0)*100:.1f}%")
        print(f"  • Сигналов отправлено: {self.stats.get('signals_sent_46plus', 0)}")
        print(f"  • Отфильтровано: {self.stats.get('signals_filtered_out', 0)}")
        
        self.analyze_match_selection()
        self.analyze_accuracy_by_confidence()
        self.analyze_accuracy_by_minute()
        self.analyze_self_learning()
        self.analyze_feature_importance()
        self.generate_recommendations()
        
        print("\n" + "="*80)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("="*80)

if __name__ == "__main__":
    analyzer = SystemAnalyzer()
    analyzer.run_full_analysis()