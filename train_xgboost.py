# train_xgboost.py
import json
import numpy as np
import joblib
from predictor import Predictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_from_history():
    """Обучает XGBoost на сохраненной истории предсказаний"""
    
    # Загружаем предиктор
    predictor = Predictor()
    
    # Загружаем историю
    predictor.load_predictions()
    
    if len(predictor.predictions_history) < 100:
        logger.error(f"❌ Недостаточно данных в истории: {len(predictor.predictions_history)} < 100")
        logger.info("Запустите бота в режиме сбора данных на несколько дней")
        return
    
    logger.info(f"📊 Найдено {len(predictor.predictions_history)} матчей в истории")
    
    # Обучаем модель
    success = predictor._train_xgboost_on_history()
    
    if success:
        logger.info("✅ XGBoost модель успешно обучена и сохранена")
    else:
        logger.error("❌ Не удалось обучить модель")

if __name__ == "__main__":
    train_from_history()