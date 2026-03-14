import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import json
import os

from models import Match, TeamStats
from team_form import TeamFormAnalyzer

logger = logging.getLogger(__name__)

class FootballPredictor:
    """
    Класс для прогнозирования голов в футбольных матчах на основе статистики.
    Использует взвешенный подход с учетом xG, ударов, формы команд и других метрик.
    """
    
    def __init__(self):
        # Веса для различных факторов при расчете вероятности гола
        # Оптимизированные веса на основе анализа
        self.weights = {
            'xg': 0.28,              # xG - самый важный фактор
            'shots_ontarget': 0.18,   # Удары в створ
            'team_form': 0.15,        # Форма команд
            'dangerous_attacks': 0.12, # Опасные атаки
            'shots': 0.10,            # Все удары
            'corners': 0.09,          # Угловые
            'possession': 0.05,       # Владение
            'h2h': 0.03                # История встреч
        }
        
        # Пороговые значения для генерации сигналов
        self.thresholds = {
            'low': 0.15,    # Минимальная вероятность для уведомления
            'medium': 0.25,  # Средняя вероятность
            'high': 0.35,    # Высокая вероятность
            'very_high': 0.45 # Очень высокая вероятность
        }
        
        # История предсказаний для самообучения
        self.predictions_history = []
        self.max_history_size = 1000
        
        # Инициализация анализатора формы команд
        self.team_analyzer = TeamFormAnalyzer()
        
        logger.info("FootballPredictor инициализирован с весами: %s", self.weights)
    
    def predict_match(self, match: Match) -> Dict:
        """
        Основной метод для предсказания вероятности голов в матче
        
        Args:
            match: Объект Match с данными о матче
            
        Returns:
            Dict с результатами анализа
        """
        try:
            # Получаем данные статистики для обеих команд
            home_stats = self._extract_team_stats(match, is_home=True)
            away_stats = self._extract_team_stats(match, is_home=False)
            
            # Получаем форму команд, если доступны ID
            home_form = None
            away_form = None
            
            if match.home_team and match.home_team.id:
                home_form = self.team_analyzer.get_team_form(match.home_team.id)
                
            if match.away_team and match.away_team.id:
                away_form = self.team_analyzer.get_team_form(match.away_team.id)
            
            # Рассчитываем вероятности голов для каждой команды
            home_goal_prob = self._calculate_goal_probability(home_stats, is_home=True, team_form=home_form)
            away_goal_prob = self._calculate_goal_probability(away_stats, is_home=False, team_form=away_form)
            
            # Рассчитываем общую вероятность гола в матче
            total_goal_prob = self._calculate_total_goal_probability(home_goal_prob, away_goal_prob)
            
            # Определяем уровень уверенности и сигнал
            confidence_level = self._determine_confidence_level(total_goal_prob)
            signal = self._generate_signal(match, home_goal_prob, away_goal_prob, total_goal_prob, confidence_level)
            
            # Создаем результат
            result = {
                'match_id': match.id,
                'match': match,
                'home_team': match.home_team.name if match.home_team else 'Unknown',
                'away_team': match.away_team.name if match.away_team else 'Unknown',
                'home_goal_probability': round(home_goal_prob, 3),
                'away_goal_probability': round(away_goal_prob, 3),
                'total_goal_probability': round(total_goal_prob, 3),
                'confidence_level': confidence_level,
                'signal': signal,
                'home_stats': home_stats,
                'away_stats': away_stats,
                'home_form': home_form,
                'away_form': away_form,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при предсказании матча {match.id}: {e}")
            return self._get_default_prediction(match)
    
    def _calculate_goal_probability(self, stats: Dict, is_home: bool = True, team_form: Optional[Dict] = None) -> float:
        """
        Рассчитывает вероятность гола для одной команды на основе статистики
        
        Args:
            stats: Словарь со статистикой команды
            is_home: Флаг домашней команды
            team_form: Данные о форме команды
            
        Returns:
            float: Вероятность гола от 0 до 1
        """
        factors = []
        total_weight = 0
        
        # Базовые факторы из статистики
        factor_mappings = [
            ('xg', 'xg', 0.3),
            ('shots_ontarget', 'shots_on_target', 0.2),
            ('dangerous_attacks', 'dangerous_attacks', 0.15),
            ('shots', 'shots', 0.1),
            ('corners', 'corners', 0.08),
            ('possession', 'possession', 0.05)
        ]
        
        for key, stat_key, default_weight in factor_mappings:
            if key in self.weights:
                weight = self.weights[key]
                stat_value = stats.get(stat_key, 0)
                
                # Нормализация значений
                if key == 'xg':
                    normalized = min(stat_value / 3.0, 1.0)  # Обычно xG редко > 3
                elif key == 'shots_ontarget':
                    normalized = min(stat_value / 10.0, 1.0)
                elif key == 'dangerous_attacks':
                    normalized = min(stat_value / 50.0, 1.0)
                elif key == 'shots':
                    normalized = min(stat_value / 20.0, 1.0)
                elif key == 'corners':
                    normalized = min(stat_value / 10.0, 1.0)
                elif key == 'possession':
                    normalized = stat_value / 100.0
                else:
                    normalized = 0.5
                
                factors.append(normalized * weight)
                total_weight += weight
        
        # Добавляем фактор формы команды
        if team_form and 'team_form' in self.weights:
            form_factor = team_form.get('form', 0.5)
            factors.append(form_factor * self.weights['team_form'])
            total_weight += self.weights['team_form']
        
        # Добавляем бонус домашней команды
        if is_home:
            home_bonus = 0.05
            factors.append(home_bonus)
            total_weight += 0.05
        
        # Рассчитываем итоговую вероятность
        if total_weight > 0:
            probability = sum(factors) / total_weight
        else:
            probability = 0.3  # Значение по умолчанию
        
        # Ограничиваем от 0.05 до 0.95
        return max(0.05, min(0.95, probability))
    
    def _calculate_total_goal_probability(self, home_prob: float, away_prob: float) -> float:
        """
        Рассчитывает общую вероятность гола в матче
        
        Args:
            home_prob: Вероятность гола хозяев
            away_prob: Вероятность гола гостей
            
        Returns:
            float: Общая вероятность гола
        """
        # Вероятность того, что забьют хотя бы одни
        total_prob = 1 - (1 - home_prob) * (1 - away_prob)
        
        # Корректировка на основе исторических данных
        # В среднем в матче забивается ~2.5 гола, что дает вероятность ~0.92
        # Если вероятность слишком низкая или высокая, корректируем
        
        if total_prob > 0.95:
            total_prob = 0.95
        elif total_prob < 0.3:
            # Если вероятность очень низкая, немного повышаем
            total_prob = total_prob * 1.2
        
        return total_prob
    
    def _determine_confidence_level(self, probability: float) -> str:
        """
        Определяет уровень уверенности на основе вероятности
        
        Args:
            probability: Вероятность гола
            
        Returns:
            str: Уровень уверенности (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)
        """
        if probability >= 0.45:
            return "VERY_HIGH"
        elif probability >= 0.35:
            return "HIGH"
        elif probability >= 0.25:
            return "MEDIUM"
        elif probability >= 0.15:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _generate_signal(self, match: Match, home_prob: float, away_prob: float, 
                        total_prob: float, confidence: str) -> Dict:
        """
        Генерирует сигнал для отправки в Telegram
        
        Args:
            match: Объект матча
            home_prob: Вероятность гола хозяев
            away_prob: Вероятность гола гостей
            total_prob: Общая вероятность
            confidence: Уровень уверенности
            
        Returns:
            Dict с данными сигнала
        """
        # Определяем эмодзи в зависимости от уровня уверенности
        confidence_emojis = {
            "VERY_HIGH": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "VERY_LOW": "⚪"
        }
        
        emoji = confidence_emojis.get(confidence, "⚪")
        
        # Формируем текст сигнала
        home_name = match.home_team.name if match.home_team else "Home"
        away_name = match.away_team.name if match.away_team else "Away"
        
        # Определяем, какая команда с большей вероятностью забьет
        if home_prob > away_prob + 0.1:
            team_focus = f"⚽ {home_name}"
        elif away_prob > home_prob + 0.1:
            team_focus = f"⚽ {away_name}"
        else:
            team_focus = "⚽ Обе команды"
        
        # Формируем сообщение
        message = (
            f"{emoji} <b>Потенциальный гол!</b>\n"
            f"{home_name} vs {away_name}\n\n"
            f"📊 <b>Вероятность гола:</b> {total_prob*100:.1f}%\n"
            f"🎯 <b>Уверенность:</b> {confidence}\n"
            f"👥 {team_focus}\n\n"
            f"🏠 {home_name}: {home_prob*100:.1f}%\n"
            f"✈️ {away_name}: {away_prob*100:.1f}%"
        )
        
        # Добавляем время матча, если есть
        if match.start_time:
            message += f"\n⏱ Начало: {match.start_time.strftime('%H:%M')}"
        
        signal = {
            'emoji': emoji,
            'message': message,
            'confidence': confidence,
            'probability': total_prob,
            'home_prob': home_prob,
            'away_prob': away_prob,
            'match_id': match.id,
            'timestamp': datetime.now()
        }
        
        return signal
    
    def _extract_team_stats(self, match: Match, is_home: bool) -> Dict:
        """
        Извлекает статистику для команды из объекта матча
        
        Args:
            match: Объект матча
            is_home: True для домашней команды, False для гостей
            
        Returns:
            Dict со статистикой
        """
        stats = {
            'shots': 0,
            'shots_on_target': 0,
            'corners': 0,
            'possession': 50,
            'dangerous_attacks': 0,
            'xg': 0.5
        }
        
        if not match.stats:
            return stats
        
        # Пытаемся найти статистику для нужной команды
        team_id = match.home_team.id if is_home else match.away_team.id
        
        for period_stats in match.stats:
            if period_stats.get('period') == 'ALL':
                for team_stat in period_stats.get('groups', []):
                    if team_stat.get('teamId') == team_id:
                        items = team_stat.get('statisticsItems', [])
                        for item in items:
                            name = item.get('name', '').lower()
                            value = item.get('value', 0)
                            
                            # Парсим значение (может быть строкой с процентами)
                            if isinstance(value, str):
                                try:
                                    if '%' in value:
                                        value = float(value.replace('%', ''))
                                    else:
                                        value = float(value)
                                except:
                                    value = 0
                            
                            # Маппинг названий статистики
                            if 'shots on target' in name or 'удары в створ' in name:
                                stats['shots_on_target'] = value
                            elif 'total shots' in name or 'всего ударов' in name:
                                stats['shots'] = value
                            elif 'corner kicks' in name or 'угловые' in name:
                                stats['corners'] = value
                            elif 'possession' in name or 'владение' in name:
                                stats['possession'] = value
                            elif 'dangerous attacks' in name or 'опасные атаки' in name:
                                stats['dangerous_attacks'] = value
                            elif 'xg' in name or 'expected goals' in name:
                                stats['xg'] = value
        
        return stats
    
    def _add_to_history(self, prediction: Dict):
        """Добавляет предсказание в историю"""
        self.predictions_history.append(prediction)
        
        # Ограничиваем размер истории
        if len(self.predictions_history) > self.max_history_size:
            self.predictions_history = self.predictions_history[-self.max_history_size:]
    
    def _get_default_prediction(self, match: Match) -> Dict:
        """Возвращает предсказание по умолчанию в случае ошибки"""
        return {
            'match_id': match.id,
            'match': match,
            'home_team': match.home_team.name if match.home_team else 'Unknown',
            'away_team': match.away_team.name if match.away_team else 'Unknown',
            'home_goal_probability': 0.3,
            'away_goal_probability': 0.3,
            'total_goal_probability': 0.5,
            'confidence_level': 'LOW',
            'signal': None,
            'home_stats': {},
            'away_stats': {},
            'error': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_live_match(self, match: Match) -> Optional[Dict]:
        """
        Анализирует live-матч и генерирует сигнал при необходимости
        
        Args:
            match: Объект live-матча
            
        Returns:
            Dict с сигналом или None
        """
        try:
            # Получаем предсказание
            prediction = self.predict_match(match)
            
            # Проверяем, нужно ли отправить сигнал
            if self._should_send_signal(prediction):
                logger.info(f"Сгенерирован сигнал для матча {match.id} с вероятностью {prediction['total_goal_probability']:.2f}")
                
                # Если матч завершен, сохраняем в историю
                if match.is_finished and hasattr(self, 'team_analyzer'):
                    try:
                        self.team_analyzer.save_match(
                            match_id=match.id,
                            home_id=match.home_team.id,
                            away_id=match.away_team.id,
                            home_score=match.home_score,
                            away_score=match.away_score,
                            match_date=match.start_time or datetime.now(),
                            league_id=match.league_id
                        )
                        logger.debug(f"📊 Матч {match.id} сохранен в историю")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения матча {match.id} в историю: {e}")
                
                return prediction.get('signal')
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при анализе live-матча {match.id}: {e}")
            return None
    
    def _should_send_signal(self, prediction: Dict) -> bool:
        """
        Определяет, нужно ли отправлять сигнал на основе предсказания
        
        Args:
            prediction: Результат предсказания
            
        Returns:
            bool: True если нужно отправить сигнал
        """
        # Не отправляем сигналы для ошибочных предсказаний
        if prediction.get('error', False):
            return False
        
        # Проверяем вероятность
        probability = prediction.get('total_goal_probability', 0)
        confidence = prediction.get('confidence_level', 'LOW')
        
        # Отправляем сигнал для HIGH и VERY_HIGH уверенности
        if confidence in ['HIGH', 'VERY_HIGH']:
            return True
        
        # Для MEDIUM отправляем только если вероятность выше порога
        if confidence == 'MEDIUM' and probability >= self.thresholds['medium']:
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Возвращает статистику работы предсказателя
        
        Returns:
            Dict со статистикой
        """
        if not self.predictions_history:
            return {
                'total_predictions': 0,
                'avg_probability': 0,
                'signals_sent': 0,
                'confidence_distribution': {}
            }
        
        total = len(self.predictions_history)
        signals = [p for p in self.predictions_history if p.get('signal')]
        
        # Распределение по уровням уверенности
        confidence_dist = defaultdict(int)
        for p in self.predictions_history:
            confidence_dist[p.get('confidence_level', 'UNKNOWN')] += 1
        
        # Нормализуем
        for k in confidence_dist:
            confidence_dist[k] = confidence_dist[k] / total
        
        return {
            'total_predictions': total,
            'avg_probability': np.mean([p.get('total_goal_probability', 0) for p in self.predictions_history]),
            'signals_sent': len(signals),
            'signal_rate': len(signals) / total if total > 0 else 0,
            'confidence_distribution': dict(confidence_dist)
        }
    
    def update_weights(self, new_weights: Dict):
        """
        Обновляет веса факторов (для самообучения)
        
        Args:
            new_weights: Новые веса
        """
        # Нормализуем веса, чтобы сумма была 1
        total = sum(new_weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in new_weights.items()}
            logger.info(f"Веса обновлены: {self.weights}")
    
    def save_predictions(self, filename: str = 'data/predictions.json'):
        """Сохраняет историю предсказаний в файл"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Конвертируем в сериализуемый формат
            serializable = []
            for p in self.predictions_history:
                p_copy = p.copy()
                # Удаляем несериализуемые объекты
                if 'match' in p_copy:
                    del p_copy['match']
                if 'signal' in p_copy and p_copy['signal']:
                    if 'timestamp' in p_copy['signal']:
                        p_copy['signal']['timestamp'] = p_copy['signal']['timestamp'].isoformat()
                serializable.append(p_copy)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Сохранено {len(serializable)} предсказаний в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения предсказаний: {e}")
    
    def load_predictions(self, filename: str = 'data/predictions.json'):
        """Загружает историю предсказаний из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.predictions_history = data
                logger.info(f"Загружено {len(data)} предсказаний из {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки предсказаний: {e}")