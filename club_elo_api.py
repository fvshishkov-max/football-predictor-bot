# club_elo_api.py
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
import sqlite3

logger = logging.getLogger(__name__)

class ClubEloClient:
    """
    Клиент для API ClubElo (http://clubelo.com/API)
    Предоставляет Elo рейтинги и вероятности матчей
    """
    
    BASE_URL = "http://api.clubelo.com"
    
    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 секунды между запросами (будьте вежливы)
        
    async def _make_request(self, endpoint: str) -> Optional[Any]:
        """Выполняет запрос к API ClubElo"""
        
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            logger.debug(f"⏳ Ожидание {wait_time:.1f}с перед запросом к ClubElo")
            await asyncio.sleep(wait_time)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        timeout = aiohttp.ClientTimeout(total=30)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"📡 Запрос к ClubElo: {url}")
                    async with session.get(url) as response:
                        
                        self.last_request_time = datetime.now().timestamp()
                        
                        if response.status == 429:
                            retry_after = 60
                            logger.warning(f"⚠️ Rate limit (429), ожидание {retry_after}с")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status != 200:
                            logger.error(f"❌ Ошибка API {response.status} для {url}")
                            return None
                        
                        # ClubElo возвращает CSV или текст
                        text = await response.text()
                        
                        # Парсим CSV
                        lines = text.strip().split('\n')
                        if len(lines) > 1:
                            headers = lines[0].split(',')
                            data = []
                            for line in lines[1:]:
                                values = line.split(',')
                                if len(values) == len(headers):
                                    row = dict(zip(headers, values))
                                    data.append(row)
                            return data
                        return lines
                        
            except asyncio.TimeoutError:
                logger.error(f"⏰ Таймаут запроса к {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Ошибка запроса: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        
        return None
    
    async def get_club_history(self, club_name: str) -> Optional[List[Dict]]:
        """
        Получает историю Elo рейтинга клуба
        
        Args:
            club_name: Название клуба (например, "Arsenal", "Barcelona")
            
        Returns:
            List[Dict] с историей рейтинга
        """
        # Обрабатываем название для URL
        club_name = club_name.replace(' ', '%20')
        data = await self._make_request(f"/{club_name}")
        
        if data and isinstance(data, list):
            logger.info(f"✅ Получена история Elo для {club_name}: {len(data)} записей")
            return data
        return None
    
    async def get_upcoming_fixtures(self) -> Optional[List[Dict]]:
        """
        Получает вероятности для всех предстоящих матчей
        
        Returns:
            List[Dict] с вероятностями матчей
        """
        data = await self._make_request("/Fixtures")
        
        if data and isinstance(data, list):
            logger.info(f"✅ Получены предстоящие матчи: {len(data)} игр")
            return data
        return None
    
    async def get_ranking_by_date(self, date: datetime) -> Optional[List[Dict]]:
        """
        Получает рейтинг всех клубов на указанную дату
        
        Args:
            date: Дата в формате YYYY-MM-DD
            
        Returns:
            List[Dict] с рейтингом клубов
        """
        date_str = date.strftime("%Y-%m-%d")
        data = await self._make_request(f"/{date_str}")
        
        if data and isinstance(data, list):
            logger.info(f"✅ Получен рейтинг на {date_str}: {len(data)} клубов")
            return data
        return None


class EloAnalyzer:
    """
    Анализирует Elo рейтинги для улучшения прогнозов
    """
    
    def __init__(self):
        self.club_elo = ClubEloClient()
        self.cache = {}
        
    async def get_team_strength(self, team_name: str) -> Optional[float]:
        """
        Получает текущую силу команды на основе Elo
        
        Args:
            team_name: Название команды
            
        Returns:
            float: Elo рейтинг или None
        """
        try:
            history = await self.club_elo.get_club_history(team_name)
            if history and len(history) > 0:
                # Последняя запись - текущий рейтинг
                latest = history[-1]
                return float(latest.get('Elo', 0))
        except Exception as e:
            logger.error(f"Ошибка получения Elo для {team_name}: {e}")
        return None
    
    async def get_team_form_trend(self, team_name: str, days: int = 90) -> Dict:
        """
        Анализирует тренд формы команды на основе Elo
        
        Args:
            team_name: Название команды
            days: Количество дней для анализа
            
        Returns:
            Dict с информацией о тренде
        """
        try:
            history = await self.club_elo.get_club_history(team_name)
            if not history or len(history) < 2:
                return {'trend': 0, 'volatility': 0, 'current_elo': 1500}
            
            # Конвертируем в список с числами
            elo_values = []
            dates = []
            for record in history[-days:]:  # Последние N дней
                try:
                    elo_values.append(float(record.get('Elo', 1500)))
                    dates.append(record.get('From', ''))
                except:
                    pass
            
            if len(elo_values) < 2:
                return {'trend': 0, 'volatility': 0, 'current_elo': elo_values[-1] if elo_values else 1500}
            
            # Вычисляем тренд (линейная регрессия)
            import numpy as np
            x = np.arange(len(elo_values))
            y = np.array(elo_values)
            
            # Коэффициент наклона
            slope = np.polyfit(x, y, 1)[0]
            
            # Волатильность (стандартное отклонение)
            volatility = np.std(elo_values)
            
            # Текущий Elo
            current_elo = elo_values[-1]
            
            # Определяем тренд
            if slope > 0.5:
                trend = 1  # Растущая форма
            elif slope < -0.5:
                trend = -1  # Падающая форма
            else:
                trend = 0  # Стабильная
            
            return {
                'trend': trend,
                'slope': slope,
                'volatility': volatility,
                'current_elo': current_elo,
                'min_elo': min(elo_values),
                'max_elo': max(elo_values),
                'samples': len(elo_values)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа тренда для {team_name}: {e}")
            return {'trend': 0, 'volatility': 0, 'current_elo': 1500}
    
    def calculate_win_probability(self, home_elo: float, away_elo: float) -> Dict:
        """
        Рассчитывает вероятности исхода матча на основе Elo
        
        Args:
            home_elo: Elo рейтинг хозяев
            away_elo: Elo рейтинг гостей
            
        Returns:
            Dict с вероятностями
        """
        # Добавляем преимущество домашнего поля (около 50 пунктов Elo)
        home_advantage = 50
        adjusted_home = home_elo + home_advantage
        
        # Рассчитываем ожидаемый результат
        expected_home = 1 / (1 + 10 ** ((away_elo - adjusted_home) / 400))
        expected_away = 1 - expected_home
        
        # Немного корректируем на ничью (в Elo нет ничьей)
        # Примерное распределение: 45% победа хозяев, 30% ничья, 25% победа гостей
        home_win = expected_home * 0.8
        away_win = expected_away * 0.8
        draw = 1 - home_win - away_win
        
        return {
            'home_win': round(home_win * 100, 1),
            'draw': round(draw * 100, 1),
            'away_win': round(away_win * 100, 1),
            'home_elo': home_elo,
            'away_elo': away_elo,
            'adjusted_home': adjusted_home
        }
    
    def analyze_fixture_probabilities(self, fixture_data: Dict) -> Dict:
        """
        Анализирует данные о вероятностях из API ClubElo
        
        Args:
            fixture_data: Строка с данными о матче из /Fixtures
            
        Returns:
            Dict с расшифрованными вероятностями
        """
        try:
            # Парсим строку (формат CSV)
            # Пример: "2024-03-20,Arsenal,Chelsea,2.5,1.8,3.2,0.15,0.20,0.25,0.18,0.12,0.05,0.03,0.01,0.01"
            parts = fixture_data if isinstance(fixture_data, list) else str(fixture_data).split(',')
            
            if len(parts) < 5:
                return {}
            
            date = parts[0]
            home = parts[1]
            away = parts[2]
            
            # Вероятности для разниц голов
            # Индексы могут отличаться, нужно смотреть документацию
            goal_diff_probs = {}
            for i in range(3, min(len(parts), 15)):
                try:
                    prob = float(parts[i])
                    goal_diff = i - 7  # Примерное смещение
                    goal_diff_probs[goal_diff] = prob
                except:
                    pass
            
            # Вычисляем традиционные коэффициенты 1X2
            home_win_prob = sum(v for k, v in goal_diff_probs.items() if k > 0)
            away_win_prob = sum(v for k, v in goal_diff_probs.items() if k < 0)
            draw_prob = goal_diff_probs.get(0, 0)
            
            return {
                'date': date,
                'home': home,
                'away': away,
                'probabilities': {
                    'home_win': round(home_win_prob * 100, 1),
                    'draw': round(draw_prob * 100, 1),
                    'away_win': round(away_win_prob * 100, 1),
                },
                'goal_diff_probabilities': goal_diff_probs
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа fixture: {e}")
            return {}


class IntegratedEloPredictor:
    """
    Интегрирует Elo рейтинги в существующую систему прогнозов
    """
    
    def __init__(self, predictor):
        self.elo_analyzer = EloAnalyzer()
        self.predictor = predictor
        self.elo_weight = 0.15  # Вес Elo в общем прогнозе
        
    async def enhance_prediction(self, match, base_prediction: Dict) -> Dict:
        """
        Улучшает существующий прогноз с помощью Elo данных
        
        Args:
            match: Объект матча
            base_prediction: Базовый прогноз от predictor.py
            
        Returns:
            Dict с улучшенным прогнозом
        """
        try:
            # Получаем Elo для команд
            home_elo = await self.elo_analyzer.get_team_strength(match.home_team.name)
            away_elo = await self.elo_analyzer.get_team_strength(match.away_team.name)
            
            if not home_elo or not away_elo:
                logger.debug(f"Elo данные недоступны для матча {match.id}")
                return base_prediction
            
            # Получаем тренды формы
            home_trend = await self.elo_analyzer.get_team_form_trend(match.home_team.name)
            away_trend = await self.elo_analyzer.get_team_form_trend(match.away_team.name)
            
            # Рассчитываем Elo-вероятности
            elo_probs = self.elo_analyzer.calculate_win_probability(home_elo, away_elo)
            
            # Комбинируем с базовым прогнозом
            base_home_prob = base_prediction.get('home_goal_probability', 0.3)
            base_away_prob = base_prediction.get('away_goal_probability', 0.3)
            
            # Нормализуем Elo вероятности в формат вероятности гола
            elo_home_goal_prob = elo_probs['home_win'] / 100 * 0.7 + 0.15
            elo_away_goal_prob = elo_probs['away_win'] / 100 * 0.7 + 0.15
            
            # Корректируем на тренды
            if home_trend['trend'] > 0:
                elo_home_goal_prob *= 1.1
            elif home_trend['trend'] < 0:
                elo_home_goal_prob *= 0.9
                
            if away_trend['trend'] > 0:
                elo_away_goal_prob *= 1.1
            elif away_trend['trend'] < 0:
                elo_away_goal_prob *= 0.9
            
            # Взвешенное среднее
            enhanced_home_prob = (1 - self.elo_weight) * base_home_prob + self.elo_weight * elo_home_goal_prob
            enhanced_away_prob = (1 - self.elo_weight) * base_away_prob + self.elo_weight * elo_away_goal_prob
            
            # Обновляем предсказание
            enhanced_prediction = base_prediction.copy()
            enhanced_prediction['home_goal_probability'] = min(0.8, max(0.1, enhanced_home_prob))
            enhanced_prediction['away_goal_probability'] = min(0.8, max(0.1, enhanced_away_prob))
            
            # Пересчитываем общую вероятность
            total_prob = 1 - (1 - enhanced_home_prob) * (1 - enhanced_away_prob)
            enhanced_prediction['total_goal_probability'] = min(0.95, total_prob)
            
            # Добавляем Elo информацию
            enhanced_prediction['elo_data'] = {
                'home_elo': home_elo,
                'away_elo': away_elo,
                'home_trend': home_trend['trend'],
                'away_trend': away_trend['trend'],
                'elo_probs': elo_probs,
                'weight': self.elo_weight
            }
            
            logger.info(f"📊 Elo улучшение для матча {match.id}: "
                       f"{home_elo:.0f} vs {away_elo:.0f}, "
                       f"вес {self.elo_weight}")
            
            return enhanced_prediction
            
        except Exception as e:
            logger.error(f"Ошибка Elo улучшения: {e}")
            return base_prediction
    
    async def get_upcoming_predictions(self) -> List[Dict]:
        """
        Получает прогнозы на все предстоящие матчи из ClubElo
        
        Returns:
            List[Dict] с прогнозами
        """
        try:
            fixtures = await self.elo_analyzer.club_elo.get_upcoming_fixtures()
            if not fixtures:
                return []
            
            predictions = []
            for fixture in fixtures:
                analysis = self.elo_analyzer.analyze_fixture_probabilities(fixture)
                if analysis:
                    predictions.append(analysis)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Ошибка получения предстоящих прогнозов: {e}")
            return []