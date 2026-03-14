# ml_predictor.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MLPredictor:
    """Прогнозирование голов с использованием машинного обучения"""
    
    def __init__(self, model_path: str = 'data/ml_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'minute', 'shots_home', 'shots_away', 
            'shots_ontarget_home', 'shots_ontarget_away',
            'corners_home', 'corners_away',
            'dangerous_attacks_home', 'dangerous_attacks_away',
            'possession_home', 'possession_away',
            'goals_home', 'goals_away',
            'xg_home', 'xg_away',
            'xg_remaining', 'time_ratio'
        ]
        self.training_data = []
        self.training_labels = []
        
        # Загружаем модель если есть
        self.load_model()
    
    def extract_features(self, stats: Dict, xg_data: Optional[Dict] = None) -> np.array:
        """Извлекает признаки из статистики матча"""
        features = []
        
        # Основные признаки
        features.append(stats.get('minute', 0))
        features.append(stats.get('shots', {}).get('home', 0))
        features.append(stats.get('shots', {}).get('away', 0))
        features.append(stats.get('shots', {}).get('ontarget_home', 0))
        features.append(stats.get('shots', {}).get('ontarget_away', 0))
        features.append(stats.get('corners', {}).get('home', 0))
        features.append(stats.get('corners', {}).get('away', 0))
        features.append(stats.get('dangerous_attacks', {}).get('home', 0))
        features.append(stats.get('dangerous_attacks', {}).get('away', 0))
        features.append(stats.get('possession', {}).get('home', 50))
        features.append(stats.get('possession', {}).get('away', 50))
        
        # Голы
        features.append(stats.get('goals', {}).get('home', 0))
        features.append(stats.get('goals', {}).get('away', 0))
        
        # xG если есть
        if xg_data:
            features.append(xg_data.get('home_xg', 0))
            features.append(xg_data.get('away_xg', 0))
            features.append(max(0, xg_data.get('total_xg', 0) - sum(features[-2:])))
        else:
            features.extend([0, 0, 0])
        
        # Отношение времени
        features.append(1.0 - (stats.get('minute', 0) / 90))
        
        return np.array(features).reshape(1, -1)
    
    def add_training_example(self, features: np.array, next_goal_minute: int):
        """Добавляет пример для обучения"""
        self.training_data.append(features.flatten())
        self.training_labels.append(next_goal_minute)
        
        # Автоматически обучаемся после накопления данных
        if len(self.training_data) >= 100:
            self.train()
    
    def train(self):
        """Обучает модель на собранных данных"""
        if len(self.training_data) < 10:
            logger.warning("Недостаточно данных для обучения")
            return
        
        X = np.array(self.training_data)
        y = np.array(self.training_labels)
        
        # Нормализуем признаки
        X_scaled = self.scaler.fit_transform(X)
        
        # Обучаем модель
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Разделяем на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Оцениваем качество
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        logger.info(f"✅ Модель обучена. Train score: {train_score:.3f}, Test score: {test_score:.3f}")
        
        # Сохраняем модель
        self.save_model()
    
    def predict(self, features: np.array) -> Tuple[float, float]:
        """Предсказывает время следующего гола и уверенность"""
        if self.model is None:
            return 45.0, 0.5  # Дефолтное предсказание
        
        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]
        
        # Получаем уверенность из деревьев
        predictions = [tree.predict(features_scaled)[0] for tree in self.model.estimators_]
        confidence = 1.0 - (np.std(predictions) / 45.0)  # Нормализуем
        
        return prediction, min(0.95, max(0.3, confidence))
    
    def save_model(self):
        """Сохраняет модель в файл"""
        try:
            os.makedirs('data', exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_samples': len(self.training_data)
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"💾 Модель сохранена: {self.model_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения модели: {e}")
    
    def load_model(self):
        """Загружает модель из файла"""
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                logger.info(f"📥 Модель загружена: {self.model_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {e}")
                
        def extract_enhanced_features(self, match: Match, stats: LiveStats, 
                                   xg_data: Optional[XGData] = None) -> np.array:
            """Расширенное извлечение признаков"""
            features = []
            
            # Текущая статистика матча
            features.extend(self.extract_features(stats, xg_data))
            
            # Исторические данные команд
            # (нужно добавить в базу данных)
            home_form = self.get_team_form(match.home_team.id, last_n=5)
            away_form = self.get_team_form(match.away_team.id, last_n=5)
            features.extend([home_form, away_form])
            
            # Личные встречи
            h2h_stats = self.get_h2h_stats(match.home_team.id, match.away_team.id)
            features.extend([
                h2h_stats.get('home_wins', 0),
                h2h_stats.get('away_wins', 0),
                h2h_stats.get('draws', 0),
                h2h_stats.get('avg_goals', 0)
            ])
            
            return np.array(features)