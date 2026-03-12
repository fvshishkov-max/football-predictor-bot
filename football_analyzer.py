import pandas as pd
import numpy as np
from datetime import datetime
import json
import time
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
import warnings
warnings.filterwarnings('ignore')

class LiveFootballAnalyzer:
    def __init__(self, model_path='models/'):
        self.match_history = []
        self.goal_alerts = []
        self.prediction_results = []
        self.model_path = model_path
        self.models_loaded = False
        
        # Создаем папку для моделей
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        
        # Инициализируем модели машинного обучения
        self.goal_timing_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.goal_probability_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.interval_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Загружаем обученные модели если есть
        self.load_models()
        
        # Данные для обучения
        self.training_data = []
        self.training_labels = []
        
    def load_models(self):
        """Загрузка обученных моделей"""
        try:
            if os.path.exists(f"{self.model_path}goal_timing.pkl"):
                with open(f"{self.model_path}goal_timing.pkl", 'rb') as f:
                    self.goal_timing_model = pickle.load(f)
                self.models_loaded = True
                print("✅ Модели успешно загружены")
        except:
            print("⚠️ Модели не найдены, будут созданы новые")
    
    def save_models(self):
        """Сохранение обученных моделей"""
        with open(f"{self.model_path}goal_timing.pkl", 'wb') as f:
            pickle.dump(self.goal_timing_model, f)
        with open(f"{self.model_path}goal_probability.pkl", 'wb') as f:
            pickle.dump(self.goal_probability_model, f)
        print("✅ Модели сохранены")
    
    def extract_features(self, match_data):
        """Извлечение признаков для моделей"""
        features = []
        
        # Текущая минута
        current_minute = match_data.get('current_minute', 1)
        features.append(current_minute / 90)  # Нормализация
        
        # Счет
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        features.append(home_score)
        features.append(away_score)
        features.append((home_score + away_score) / 5)  # Нормализованный тотал
        
        # Статистика ударов
        shots = match_data.get('shots', '0-0').split('-')
        shots_on_target = match_data.get('shots_on_target', '0-0').split('-')
        try:
            shots_total = int(shots[0]) + int(shots[1])
            shots_on_target_total = int(shots_on_target[0]) + int(shots_on_target[1])
            features.append(shots_total / 20)  # Нормализация
            features.append(shots_on_target_total / 10)
            features.append(shots_on_target_total / max(shots_total, 1))  # Точность
        except:
            features.extend([0, 0, 0])
        
        # Владение
        possession = match_data.get('possession', '50-50').split('-')
        try:
            poss_home = int(possession[0].replace('%',''))
            features.append(poss_home / 100)
            features.append(abs(poss_home - 50) / 50)  # Дисбаланс
        except:
            features.extend([0.5, 0])
        
        # Опасные атаки
        attacks = match_data.get('dangerous_attacks', '0-0').split('-')
        try:
            attacks_total = int(attacks[0]) + int(attacks[1])
            features.append(attacks_total / 20)
        except:
            features.append(0)
        
        # Угловые
        corners = match_data.get('corners', '0-0').split('-')
        try:
            corners_total = int(corners[0]) + int(corners[1])
            features.append(corners_total / 10)
        except:
            features.append(0)
        
        return np.array(features)
    
    def analyze_live_match(self, match_data):
        """Анализ матча в реальном времени"""
        
        current_minute = match_data.get('current_minute', 1)
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        
        # Извлекаем признаки
        features = self.extract_features(match_data)
        
        # Анализируем статистику
        stats_analysis = self._analyze_stats(match_data)
        
        # Получаем прогнозы по интервалам
        interval_predictions = self._predict_goal_intervals(match_data, stats_analysis, features)
        
        # Оцениваем вероятность гола в ближайшее время
        goal_prediction = self._predict_goal_timing(match_data, stats_analysis, features)
        
        # Самоанализ модели
        model_confidence = self._calculate_model_confidence(features)
        
        # Формируем прогноз
        prediction = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'minute': current_minute,
            'score': f"{home_score}:{away_score}",
            'goal_alert': goal_prediction['alert'],
            'goal_minute_prediction': goal_prediction['predicted_minute'],
            'goal_likelihood': goal_prediction['likelihood'],
            'interval_predictions': interval_predictions,
            'analysis': stats_analysis['summary'],
            'key_factors': stats_analysis['key_factors'],
            'model_confidence': model_confidence,
            'recommendation': self._get_recommendation(goal_prediction, stats_analysis, interval_predictions)
        }
        
        # Если прогнозируется скорый гол - добавляем в алерты
        if goal_prediction['alert']:
            self.goal_alerts.append({
                'minute': current_minute,
                'prediction_minute': goal_prediction['predicted_minute'],
                'reason': goal_prediction['reason'],
                'confidence': model_confidence
            })
        
        self.match_history.append(prediction)
        return prediction
    
    def _predict_goal_intervals(self, match_data, stats_analysis, features):
        """Прогноз голов по интервалам"""
        current_minute = match_data.get('current_minute', 1)
        
        intervals = {
            'до 15': (1, 15),
            '16-30': (16, 30),
            '31-45': (31, 45),
            '46-60': (46, 60),
            '61-75': (61, 75),
            '76-90': (76, 90)
        }
        
        predictions = {}
        raw_data = stats_analysis['raw_data']
        
        for interval_name, (start, end) in intervals.items():
            # Пропускаем уже прошедшие интервалы
            if current_minute > end:
                predictions[interval_name] = "✅ Интервал прошел"
                continue
            
            # Рассчитываем вероятность для каждого интервала
            probability = self._calculate_interval_probability(
                interval_name, start, end, current_minute, raw_data, features
            )
            
            predictions[interval_name] = probability
        
        return predictions
    
    def _calculate_interval_probability(self, interval_name, start, end, current_minute, raw_data, features):
        """Расчет вероятности года в конкретном интервале"""
        
        base_prob = 0
        
        # Базовые вероятности для разных интервалов
        if interval_name == 'до 15':
            base_prob = 20  # 20% голов в первые 15 минут
        elif interval_name == '16-30':
            base_prob = 25
        elif interval_name == '31-45':
            base_prob = 30  # Самый результативный в 1 тайме
        elif interval_name == '46-60':
            base_prob = 20
        elif interval_name == '61-75':
            base_prob = 25
        elif interval_name == '76-90':
            base_prob = 35  # Концовка матча
        
        # Корректировка на основе текущей статистики
        if current_minute < end:
            # Если интервал еще не начался или идет
            time_factor = (end - max(current_minute, start)) / (end - start + 1)
            
            # Учитываем удары в створ
            shots_factor = min(raw_data['shots_on_target_total'] / 5, 2)
            
            # Учитываем опасные атаки
            attacks_factor = min(raw_data['attacks_total'] / 10, 2)
            
            # Учитываем общую активность
            if raw_data['shots_on_target_total'] > 3:
                base_prob *= 1.5
            elif raw_data['shots_on_target_total'] > 1:
                base_prob *= 1.2
            
            # Финальная вероятность
            probability = base_prob * time_factor * shots_factor * attacks_factor
            
            # Ограничиваем вероятность
            probability = min(max(probability, 5), 85)
            
            # Форматируем вывод
            if probability > 60:
                return f"🔥 ВЫСОКАЯ ({probability:.0f}%)"
            elif probability > 35:
                return f"📊 СРЕДНЯЯ ({probability:.0f}%)"
            else:
                return f"💤 НИЗКАЯ ({probability:.0f}%)"
        else:
            return "⏳ Ожидание"
    
    def _calculate_model_confidence(self, features):
        """Самоанализ модели - оценка уверенности в прогнозе"""
        
        # Оцениваем качество входных данных
        data_quality = 0
        reasons = []
        
        # Проверяем наличие достаточной статистики
        if features[4] > 0:  # Удары в створ
            data_quality += 20
            reasons.append("есть удары в створ")
        
        if features[6] > 0.3:  # Точность ударов
            data_quality += 15
            reasons.append("хорошая точность")
        
        if features[8] > 0.2:  # Опасные атаки
            data_quality += 20
            reasons.append("опасные атаки")
        
        if features[9] > 0.3:  # Угловые
            data_quality += 10
            reasons.append("стандарты")
        
        if features[1] + features[2] < 3:  # Небольшой счет
            data_quality += 15
            reasons.append("есть потенциал для голов")
        
        # Базовая уверенность
        base_confidence = 50 + data_quality
        
        # Если мало данных, уверенность низкая
        if features[4] == 0 and features[6] == 0:
            base_confidence = 30
            reasons = ["недостаточно статистики"]
        
        confidence_level = min(base_confidence, 95)
        
        return {
            'level': confidence_level,
            'quality': 'ВЫСОКАЯ' if confidence_level > 70 else 'СРЕДНЯЯ' if confidence_level > 45 else 'НИЗКАЯ',
            'reasons': reasons
        }
    
    def _analyze_stats(self, match_data):
        """Детальный анализ статистики матча"""
        
        # Получаем данные
        shots = match_data.get('shots', '0-0').split('-')
        shots_on_target = match_data.get('shots_on_target', '0-0').split('-')
        possession = match_data.get('possession', '50-50').split('-')
        corners = match_data.get('corners', '0-0').split('-')
        attacks = match_data.get('dangerous_attacks', '0-0').split('-')
        
        try:
            shots_home, shots_away = int(shots[0]), int(shots[1])
            shots_on_target_home, shots_on_target_away = int(shots_on_target[0]), int(shots_on_target[1])
            poss_home, poss_away = int(possession[0].replace('%','')), int(possession[1].replace('%',''))
            corners_home, corners_away = int(corners[0]), int(corners[1])
            attacks_home, attacks_away = int(attacks[0]), int(attacks[1])
        except:
            shots_home = shots_away = 0
            shots_on_target_home = shots_on_target_away = 0
            poss_home = poss_away = 50
            corners_home = corners_away = 0
            attacks_home = attacks_away = 0
        
        total_shots = shots_home + shots_away
        total_shots_on_target = shots_on_target_home + shots_on_target_away
        total_attacks = attacks_home + attacks_away
        total_corners = corners_home + corners_away
        
        # Анализ активности
        analysis = []
        key_factors = []
        
        # 1. Анализ ударов
        if total_shots_on_target >= 4:
            analysis.append(f"🔥 Очень высокая активность: {total_shots_on_target} ударов в створ")
            key_factors.append("Много ударов в створ")
        elif total_shots_on_target >= 2:
            analysis.append(f"📊 Хорошая активность: {total_shots_on_target} ударов в створ")
            key_factors.append("Есть удары в створ")
        elif total_shots_on_target >= 1:
            analysis.append(f"📈 Средняя активность: {total_shots_on_target} удар в створ")
        else:
            analysis.append("💤 Низкая активность: нет ударов в створ")
        
        # 2. Анализ атак
        if total_attacks > 10:
            analysis.append(f"⚡️ Много опасных атак ({total_attacks})")
            key_factors.append("Высокая атакующая активность")
        elif total_attacks > 5:
            analysis.append(f"📊 {total_attacks} опасных атак")
        
        # 3. Анализ точности
        if total_shots > 0:
            accuracy = (total_shots_on_target / total_shots) * 100
            if accuracy > 45:
                analysis.append(f"🎯 Отличная точность ({accuracy:.0f}%)")
                key_factors.append("Высокая точность")
            elif accuracy > 30:
                analysis.append(f"📈 Средняя точность ({accuracy:.0f}%)")
        
        # 4. Анализ владения
        if abs(poss_home - poss_away) > 20:
            dominant = "хозяева" if poss_home > poss_away else "гости"
            analysis.append(f"🎯 Доминирование {dominant} ({max(poss_home, poss_away)}%)")
            key_factors.append(f"Доминирование")
        
        # 5. Анализ стандартов
        if total_corners > 6:
            analysis.append(f"🚩 Много угловых ({total_corners})")
            key_factors.append("Стандартные положения")
        
        summary = {
            'total_shots': f"{shots_home}:{shots_away}",
            'shots_on_target': f"{shots_on_target_home}:{shots_on_target_away}",
            'possession': f"{poss_home}%:{poss_away}%",
            'corners': f"{corners_home}:{corners_away}",
            'dangerous_attacks': f"{attacks_home}:{attacks_away}",
            'analysis': analysis
        }
        
        return {
            'summary': summary,
            'key_factors': key_factors,
            'raw_data': {
                'shots_on_target_home': shots_on_target_home,
                'shots_on_target_away': shots_on_target_away,
                'shots_on_target_total': total_shots_on_target,
                'attacks_home': attacks_home,
                'attacks_away': attacks_away,
                'attacks_total': total_attacks,
                'possession_home': poss_home,
                'corners_total': total_corners
            }
        }
    
    def _predict_goal_timing(self, match_data, stats_analysis, features):
        """Прогнозирование времени следующего года"""
        
        current_minute = match_data.get('current_minute', 1)
        raw_data = stats_analysis['raw_data']
        
        # Используем модель машинного обучения если она обучена
        if self.models_loaded and len(self.training_data) > 10:
            try:
                # Предсказание с помощью модели
                pred_minute = self.goal_timing_model.predict([features])[0]
                pred_prob = self.goal_probability_model.predict_proba([features])[0][1]
                
                goal_score = pred_prob * 100
                predicted_minute = int(pred_minute)
            except:
                # Fallback на эвристики
                goal_score, predicted_minute = self._heuristic_prediction(current_minute, raw_data)
        else:
            # Используем эвристики
            goal_score, predicted_minute = self._heuristic_prediction(current_minute, raw_data)
        
        # Определяем вероятность и минуту года
        if goal_score >= 65:
            likelihood = "⚡️ ОЧЕНЬ ВЫСОКАЯ"
            alert = True
            reason = f"Экстремально высокая активность"
        elif goal_score >= 45:
            likelihood = "📈 ВЫСОКАЯ"
            alert = True
            reason = f"Стабильное давление на ворота"
        elif goal_score >= 30:
            likelihood = "📊 СРЕДНЯЯ"
            alert = False
            reason = f"Средняя активность команд"
        else:
            likelihood = "💤 НИЗКАЯ"
            alert = False
            reason = f"Низкая результативность"
        
        # Не даем прогноз больше 90 минут
        if predicted_minute > 90:
            predicted_minute = 90 + np.random.randint(0, 6)
        
        return {
            'alert': alert,
            'predicted_minute': predicted_minute,
            'likelihood': likelihood,
            'reason': reason,
            'goal_score': goal_score
        }
    
    def _heuristic_prediction(self, current_minute, raw_data):
        """Эвристический метод прогнозирования"""
        
        goal_score = 0
        
        # Фактор ударов в створ
        if raw_data['shots_on_target_total'] >= 4:
            goal_score += 50
        elif raw_data['shots_on_target_total'] >= 2:
            goal_score += 30
        elif raw_data['shots_on_target_total'] >= 1:
            goal_score += 15
        
        # Фактор опасных атак
        if raw_data['attacks_total'] >= 8:
            goal_score += 25
        elif raw_data['attacks_total'] >= 4:
            goal_score += 15
        
        # Фактор угловых
        if raw_data['corners_total'] >= 5:
            goal_score += 15
        
        # Временные факторы
        if current_minute < 20:
            # Начало матча
            if goal_score > 40:
                goal_score *= 0.8
        elif current_minute > 70:
            # Концовка
            goal_score *= 1.2
        
        # Прогноз минуты
        if goal_score >= 60:
            predicted_minute = current_minute + np.random.randint(2, 7)
        elif goal_score >= 40:
            predicted_minute = current_minute + np.random.randint(5, 12)
        elif goal_score >= 20:
            predicted_minute = current_minute + np.random.randint(10, 20)
        else:
            predicted_minute = current_minute + np.random.randint(20, 35)
        
        return goal_score, predicted_minute
    
    def _get_recommendation(self, goal_prediction, stats_analysis, interval_predictions):
        """Формирование рекомендации"""
        
        if goal_prediction['alert']:
            if goal_prediction['goal_score'] >= 65:
                return "🔥 СРОЧНО! ГОЛ В БЛИЖАЙШИЕ 5 МИНУТ"
            else:
                return f"⚽️ Ожидайте гол до {goal_prediction['predicted_minute']}' минуты"
        else:
            # Находим ближайший интервал с высокой вероятностью
            high_prob_intervals = []
            for interval, prob in interval_predictions.items():
                if "ВЫСОКАЯ" in prob and interval not in ["✅ Интервал прошел", "⏳ Ожидание"]:
                    high_prob_intervals.append(interval)
            
            if high_prob_intervals:
                return f"📊 Следите за интервалом {high_prob_intervals[0]}"
            else:
                return "⏳ Команды раскачиваются, пока низкая активность"
    
    def add_training_example(self, features, actual_goal_minute, goal_happened):
        """Добавление примера для обучения"""
        self.training_data.append(features)
        self.training_labels.append(actual_goal_minute if goal_happened else 95)  # 95 = нет года
    
    def train_models(self):
        """Обучение моделей на собранных данных"""
        if len(self.training_data) < 10:
            print("⚠️ Недостаточно данных для обучения (нужно минимум 10 примеров)")
            return False
        
        X = np.array(self.training_data)
        y = np.array(self.training_labels)
        
        # Обучаем модель времени года
        self.goal_timing_model.fit(X, y)
        
        # Обучаем модель вероятности
        y_binary = (y < 95).astype(int)  # 1 если был гол, 0 если нет
        self.goal_probability_model.fit(X, y_binary)
        
        # Оценка качества
        X_train, X_test, y_train, y_test = train_test_split(X, y_binary, test_size=0.2)
        self.interval_model.fit(X_train, y_train)
        accuracy = self.interval_model.score(X_test, y_test)
        
        self.models_loaded = True
        self.save_models()
        
        print(f"✅ Модели обучены. Точность: {accuracy:.2f}")
        return True
    
    def evaluate_prediction(self, match_id, actual_goals, actual_goal_minutes):
        """Оценка качества прогноза после матча"""
        
        evaluation = {
            'match_id': match_id,
            'actual_goals': actual_goals,
            'actual_goal_minutes': actual_goal_minutes,
            'predictions': self.match_history,
            'alerts': self.goal_alerts,
            'accuracy': {}
        }
        
        # Анализируем точность алертов
        if self.goal_alerts and actual_goal_minutes:
            correct_alerts = 0
            for alert in self.goal_alerts:
                pred_minute = alert['prediction_minute']
                # Проверяем, был ли гол в пределах 5 минут от прогноза
                for goal_minute in actual_goal_minutes:
                    if abs(pred_minute - goal_minute) <= 5:
                        correct_alerts += 1
                        break
            
            evaluation['accuracy']['alerts_accuracy'] = correct_alerts / len(self.goal_alerts) if self.goal_alerts else 0
            evaluation['accuracy']['total_alerts'] = len(self.goal_alerts)
            evaluation['accuracy']['correct_alerts'] = correct_alerts
        
        # Сохраняем результаты
        self.prediction_results.append(evaluation)
        
        return evaluation
    
    def print_live_analysis(self, prediction):
        """Красивый вывод анализа в консоль"""
        
        print("\n" + "="*70)
        print(f"⚽️ АНАЛИЗ МАТЧА [{prediction['timestamp']}]")
        print("="*70)
        print(f"⏱️ Минута: {prediction['minute']}' | Счет: {prediction['score']}")
        print("-"*70)
        
        # Статистика
        stats = prediction['analysis']
        print("📊 СТАТИСТИКА:")
        print(f"  • Удары: {stats['total_shots']} (в створ: {stats['shots_on_target']})")
        print(f"  • Владение: {stats['possession']}")
        print(f"  • Угловые: {stats['corners']}")
        print(f"  • Опасные атаки: {stats['dangerous_attacks']}")
        
        # Анализ
        print("\n🔍 АНАЛИЗ АКТИВНОСТИ:")
        for line in stats['analysis']:
            print(f"  {line}")
        
        # Уверенность модели
        conf = prediction['model_confidence']
        print(f"\n🤖 УВЕРЕННОСТЬ МОДЕЛИ: {conf['quality']} ({conf['level']:.0f}%)")
        if conf['reasons']:
            print(f"  • Основано на: {', '.join(conf['reasons'])}")
        
        # Прогноз по интервалам
        print("\n⚽️ ПРОГНОЗ ПО ИНТЕРВАЛАМ:")
        for interval, prob in prediction['interval_predictions'].items():
            print(f"  • {interval}: {prob}")
        
        # Прогноз года
        print("\n⚽️ БЛИЖАЙШИЙ ГОЛ:")
        print(f"  • Вероятность: {prediction['goal_likelihood']}")
        if prediction['goal_alert']:
            print(f"  ⚠️ СИГНАЛ! Гол до {prediction['goal_minute_prediction']}' минуты")
        else:
            print(f"  • Прогноз: ~{prediction['goal_minute_prediction']}'")
        
        # Рекомендация
        print(f"\n💡 {prediction['recommendation']}")
        print("="*70)
    
    def save_goal_alerts(self, filename='goal_alerts.json'):
        """Сохранение всех сигналов о голах"""
        if self.goal_alerts:
            report = {
                'total_alerts': len(self.goal_alerts),
                'alerts': self.goal_alerts,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Сигналы сохранены в {filename}")
    
    def save_match_history(self, filename='match_analysis.json'):
        """Сохранение всей истории анализа"""
        if self.match_history:
            output = {
                'match_history': self.match_history,
                'total_predictions': len(self.match_history),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"✅ История сохранена в {filename}")
    
    def save_prediction_results(self, filename='prediction_results.json'):
        """Сохранение результатов прогнозов"""
        if self.prediction_results:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.prediction_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Результаты прогнозов сохранены в {filename}")