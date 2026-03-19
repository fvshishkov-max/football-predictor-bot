# models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import numpy as np

@dataclass
class Team:
    """Модель команды"""
    id: int
    name: str
    country_code: Optional[str] = None
    logo_url: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id if isinstance(other, Team) else False

@dataclass
class Match:
    """Модель матча"""
    id: int
    home_team: Team
    away_team: Team
    status: int = 0
    status_name: Optional[str] = None
    minute: Optional[int] = None
    home_score: int = 0
    away_score: int = 0
    league_id: Optional[int] = None
    league_name: Optional[str] = None
    start_time: Optional[datetime] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    understat_id: Optional[int] = None
    
    # Новая расширенная статистика
    shot_timeline: List[Dict] = field(default_factory=list)  # Хронология ударов
    possession_timeline: List[Dict] = field(default_factory=list)  # Хронология владения
    pressure_timeline: List[Dict] = field(default_factory=list)  # Хронология прессинга
    passes_timeline: List[Dict] = field(default_factory=list)  # Хронология передач
    substitutions: List[Dict] = field(default_factory=list)  # Замены
    
    @property
    def is_live(self) -> bool:
        """Проверяет, идет ли матч в прямом эфире"""
        return self.status in [3, 4, 5, 6, 7, 11, 18, 19] if self.status else False
    
    @property
    def is_finished(self) -> bool:
        """Проверяет, завершен ли матч"""
        return self.status in [8, 9, 10, 17] if self.status else False
    
    @property
    def score(self) -> str:
        """Возвращает текущий счет"""
        return f"{self.home_score or 0}:{self.away_score or 0}"
    
    @property
    def total_goals(self) -> int:
        """Возвращает общее количество голов"""
        return (self.home_score or 0) + (self.away_score or 0)
    
    @property
    def time_remaining(self) -> int:
        """Возвращает оставшееся время в минутах"""
        if self.minute is None:
            return 90
        return max(0, 90 - self.minute)

@dataclass
class LiveStats:
    """Живая статистика матча"""
    minute: int
    shots_home: int = 0
    shots_away: int = 0
    shots_ontarget_home: int = 0
    shots_ontarget_away: int = 0
    possession_home: float = 50.0
    possession_away: float = 50.0
    corners_home: int = 0
    corners_away: int = 0
    fouls_home: int = 0
    fouls_away: int = 0
    yellow_cards_home: int = 0
    yellow_cards_away: int = 0
    red_cards_home: int = 0
    red_cards_away: int = 0
    dangerous_attacks_home: int = 0
    dangerous_attacks_away: int = 0
    
    # Расширенная статистика
    passes_home: int = 0
    passes_away: int = 0
    passes_accuracy_home: float = 0.0
    passes_accuracy_away: float = 0.0
    crosses_home: int = 0
    crosses_away: int = 0
    offsides_home: int = 0
    offsides_away: int = 0
    saves_home: int = 0
    saves_away: int = 0
    blocked_shots_home: int = 0
    blocked_shots_away: int = 0
    tackles_home: int = 0
    tackles_away: int = 0
    interceptions_home: int = 0
    interceptions_away: int = 0
    clearances_home: int = 0
    clearances_away: int = 0
    
    # Динамические показатели (за последние 15 минут)
    shots_last_15_home: int = 0
    shots_last_15_away: int = 0
    shots_ontarget_last_15_home: int = 0
    shots_ontarget_last_15_away: int = 0
    dangerous_attacks_last_15_home: int = 0
    dangerous_attacks_last_15_away: int = 0
    xg_last_15_home: float = 0.0
    xg_last_15_away: float = 0.0
    
    @property
    def total_shots(self) -> int:
        return self.shots_home + self.shots_away
    
    @property
    def total_shots_ontarget(self) -> int:
        return self.shots_ontarget_home + self.shots_ontarget_away
    
    @property
    def shots_accuracy(self) -> float:
        if self.total_shots > 0:
            return (self.total_shots_ontarget / self.total_shots) * 100
        return 0
    
    @property
    def total_corners(self) -> int:
        return self.corners_home + self.corners_away
    
    @property
    def total_dangerous_attacks(self) -> int:
        return self.dangerous_attacks_home + self.dangerous_attacks_away
    
    @property
    def momentum_home(self) -> float:
        """Рассчитывает momentum команды на основе последних 15 минут"""
        if self.minute < 15:
            return 0.5
        
        # Сравниваем показатели за последние 15 минут с общими
        if self.shots_last_15_home + self.shots_last_15_away > 0:
            shot_momentum = self.shots_last_15_home / (self.shots_last_15_home + self.shots_last_15_away)
        else:
            shot_momentum = 0.5
        
        if self.dangerous_attacks_last_15_home + self.dangerous_attacks_last_15_away > 0:
            attack_momentum = self.dangerous_attacks_last_15_home / (self.dangerous_attacks_last_15_home + self.dangerous_attacks_last_15_away)
        else:
            attack_momentum = 0.5
        
        if self.xg_last_15_home + self.xg_last_15_away > 0:
            xg_momentum = self.xg_last_15_home / (self.xg_last_15_home + self.xg_last_15_away)
        else:
            xg_momentum = 0.5
        
        return (shot_momentum + attack_momentum + xg_momentum) / 3
    
    @property
    def momentum_away(self) -> float:
        return 1 - self.momentum_home
    
    def to_dict(self) -> Dict:
        """Преобразует статистику в словарь"""
        return {
            'minute': self.minute,
            'shots': {
                'home': self.shots_home,
                'away': self.shots_away,
                'total': self.total_shots,
                'ontarget_home': self.shots_ontarget_home,
                'ontarget_away': self.shots_ontarget_away,
                'ontarget_total': self.total_shots_ontarget,
                'accuracy': self.shots_accuracy
            },
            'possession': {
                'home': self.possession_home,
                'away': self.possession_away
            },
            'corners': {
                'home': self.corners_home,
                'away': self.corners_away,
                'total': self.total_corners
            },
            'fouls': {
                'home': self.fouls_home,
                'away': self.fouls_away
            },
            'cards': {
                'yellow_home': self.yellow_cards_home,
                'yellow_away': self.yellow_cards_away,
                'red_home': self.red_cards_home,
                'red_away': self.red_cards_away
            },
            'dangerous_attacks': {
                'home': self.dangerous_attacks_home,
                'away': self.dangerous_attacks_away,
                'total': self.total_dangerous_attacks
            },
            'passes': {
                'home': self.passes_home,
                'away': self.passes_away,
                'accuracy_home': self.passes_accuracy_home,
                'accuracy_away': self.passes_accuracy_away
            },
            'momentum': {
                'home': self.momentum_home,
                'away': self.momentum_away,
                'shots_last_15_home': self.shots_last_15_home,
                'shots_last_15_away': self.shots_last_15_away,
                'xg_last_15_home': self.xg_last_15_home,
                'xg_last_15_away': self.xg_last_15_away
            }
        }

@dataclass
class XGData:
    """Модель для xG данных"""
    home_xg: float
    away_xg: float
    total_xg: float
    shots: Optional[int] = None
    source: Optional[str] = None
    understat_id: Optional[int] = None
    
    # Расширенные xG данные
    home_xg_by_minute: List[float] = field(default_factory=list)  # xG по минутам
    away_xg_by_minute: List[float] = field(default_factory=list)
    home_xg_by_shot: List[float] = field(default_factory=list)  # xG каждого удара
    away_xg_by_shot: List[float] = field(default_factory=list)
    
    @property
    def home_xg_formatted(self) -> str:
        return f"{self.home_xg:.2f}"
    
    @property
    def away_xg_formatted(self) -> str:
        return f"{self.away_xg:.2f}"
    
    @property
    def total_xg_formatted(self) -> str:
        return f"{self.total_xg:.2f}"
    
    @property
    def xg_per_shot_home(self) -> float:
        if self.shots and self.home_xg_by_shot:
            return sum(self.home_xg_by_shot) / len(self.home_xg_by_shot)
        return 0
    
    @property
    def xg_per_shot_away(self) -> float:
        if self.shots and self.away_xg_by_shot:
            return sum(self.away_xg_by_shot) / len(self.away_xg_by_shot)
        return 0
    
    def to_dict(self) -> Dict:
        return {
            'home_xg': self.home_xg,
            'away_xg': self.away_xg,
            'total_xg': self.total_xg,
            'shots': self.shots,
            'source': self.source,
            'understat_id': self.understat_id,
            'xg_per_shot_home': self.xg_per_shot_home,
            'xg_per_shot_away': self.xg_per_shot_away
        }

@dataclass
class GoalSignal:
    """Сигнал на гол"""
    match_id: int
    predicted_minute: int
    probability: float
    signal_type: str
    description: str
    timestamp: datetime
    stats: Dict
    minutes_left: int
    xg_data: Optional[XGData] = None
    
    # Расширенные данные сигнала
    factors_contributions: Dict = field(default_factory=dict)  # Вклад каждого фактора
    momentum_factor: float = 0.0  # Фактор momentum
    substitution_factor: float = 0.0  # Фактор замен
    
    @property
    def is_high_priority(self) -> bool:
        return self.signal_type == 'HIGH' or self.probability >= 70
    
    def to_dict(self) -> Dict:
        return {
            'match_id': self.match_id,
            'predicted_minute': self.predicted_minute,
            'probability': self.probability,
            'signal_type': self.signal_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'minutes_left': self.minutes_left,
            'is_high_priority': self.is_high_priority,
            'xg_data': self.xg_data.to_dict() if self.xg_data else None,
            'momentum_factor': self.momentum_factor,
            'substitution_factor': self.substitution_factor,
            'factors_contributions': self.factors_contributions
        }

@dataclass
class MatchAnalysis:
    """Результат анализа матча"""
    match_id: int
    timestamp: datetime
    minute: int
    score: str
    stats: LiveStats
    activity_level: str
    activity_description: str
    attack_potential: str
    next_signal: Optional[GoalSignal] = None
    has_signal: bool = False
    xg_data: Optional[XGData] = None
    
    # Расширенный анализ
    momentum_trend: str = "STABLE"  # RISING, FALLING, STABLE
    key_events: List[Dict] = field(default_factory=list)  # Ключевые события
    pressure_index: float = 0.0  # Индекс давления (0-1)
    fatigue_factor: float = 1.0  # Фактор усталости
    
    def format_telegram_message(self, match: Match) -> str:
        """Форматирует сообщение для Telegram со ссылкой на Sofascore"""
        
        home_slug = match.home_team.name.lower().replace(' ', '-').replace('.', '').replace('&', 'and')
        away_slug = match.away_team.name.lower().replace(' ', '-').replace('.', '').replace('&', 'and')
        home_slug = '-'.join(filter(None, home_slug.split('-')))
        away_slug = '-'.join(filter(None, away_slug.split('-')))
        
        sofascore_url = f"https://www.sofascore.com/ru/{home_slug}-vs-{away_slug}/{match.id}"
        
        lines = [
            f"⚽️ **{match.home_team.name} vs {match.away_team.name}**",
            f"⏱️ Минута: **{self.minute}'** | Счет: **{self.score}**",
            f"🔗 [Смотреть на Sofascore]({sofascore_url})",
            ""
        ]
        
        if self.xg_data:
            lines.append(f"📊 **xG:** {self.xg_data.home_xg_formatted} : {self.xg_data.away_xg_formatted} (всего {self.xg_data.total_xg_formatted})")
            if self.xg_data.shots:
                lines.append(f"   • Ударов: {self.xg_data.shots}")
            lines.append("")
        
        lines.append("📊 **ТЕКУЩАЯ СТАТИСТИКА:**")
        lines.append(f"   • Удары: {self.stats.shots_home}:{self.stats.shots_away} (всего {self.stats.total_shots})")
        lines.append(f"   • В створ: {self.stats.shots_ontarget_home}:{self.stats.shots_ontarget_away}")
        lines.append(f"   • Точность: {self.stats.shots_accuracy:.1f}%")
        lines.append(f"   • Владение: {self.stats.possession_home:.0f}% / {self.stats.possession_away:.0f}%")
        lines.append(f"   • Угловые: {self.stats.corners_home}:{self.stats.corners_away}")
        lines.append(f"   • Опасные атаки: {self.stats.dangerous_attacks_home}:{self.stats.dangerous_attacks_away}")
        lines.append(f"   • Пасы: {self.stats.passes_home}:{self.stats.passes_away} (точн. {self.stats.passes_accuracy_home:.0f}% / {self.stats.passes_accuracy_away:.0f}%)")
        lines.append("")
        
        # Добавляем информацию о momentum
        lines.append(f"📈 **MOMENTUM:**")
        lines.append(f"   • За последние 15 мин:")
        lines.append(f"   • Удары: {self.stats.shots_last_15_home}:{self.stats.shots_last_15_away}")
        lines.append(f"   • xG: {self.stats.xg_last_15_home:.2f}:{self.stats.xg_last_15_away:.2f}")
        lines.append(f"   • Преимущество: {self.stats.momentum_home*100:.0f}% / {self.stats.momentum_away*100:.0f}%")
        lines.append(f"   • Тренд: {self.momentum_trend}")
        lines.append("")
        
        lines.append(f"📈 **Активность:** {self.activity_level}")
        lines.append(f"💬 {self.activity_description}")
        lines.append("")
        
        if self.has_signal and self.next_signal:
            signal = self.next_signal
            lines.append(f"⚽️ **СИГНАЛ НА ГОЛ!**")
            lines.append(f"   • Ожидаемое время: **~{signal.predicted_minute}'**")
            lines.append(f"   • Вероятность: **{signal.probability:.1f}%**")
            
            if signal.factors_contributions:
                top_factors = sorted(signal.factors_contributions.items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
                lines.append(f"   • Ключевые факторы: {', '.join([f[0] for f in top_factors])}")
            
            if signal.xg_data:
                lines.append(f"   • xG: **{signal.xg_data.total_xg_formatted}**")
            
            lines.append(f"   • {signal.description}")
            
            if signal.momentum_factor > 0.1:
                lines.append(f"   • ⚡ Высокий momentum!")
            
            if signal.is_high_priority:
                lines.append("")
                lines.append("🚨 **ВЫСОКАЯ ВЕРОЯТНОСТЬ ГОЛА!**")
        else:
            lines.append("⏳ **Нет активных сигналов на гол**")
        
        lines.append("")
        lines.append(f"🔥 Атакующий потенциал: {self.attack_potential}")
        lines.append(f"📊 Индекс давления: {self.pressure_index*100:.0f}%")
        
        return '\n'.join(lines)
    
    def to_dict(self) -> Dict:
        return {
            'match_id': self.match_id,
            'timestamp': self.timestamp.isoformat(),
            'minute': self.minute,
            'score': self.score,
            'stats': self.stats.to_dict(),
            'activity_level': self.activity_level,
            'activity_description': self.activity_description,
            'attack_potential': self.attack_potential,
            'has_signal': self.has_signal,
            'next_signal': self.next_signal.to_dict() if self.next_signal else None,
            'xg_data': self.xg_data.to_dict() if self.xg_data else None,
            'momentum_trend': self.momentum_trend,
            'pressure_index': self.pressure_index,
            'fatigue_factor': self.fatigue_factor
        }

@dataclass
class Prediction:
    """Модель прогноза для UI"""
    match_id: int
    type: str
    timestamp: datetime
    next_goal_minute: Optional[int] = None
    next_goal_probability: float = 0.0
    attack_potential: str = "Средний"
    match_minute: Optional[int] = None
    current_score: str = "0:0"
    shots_stats: Dict = field(default_factory=dict)
    possession_stats: Dict = field(default_factory=dict)
    xg_total: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'match_id': self.match_id,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'next_goal_minute': self.next_goal_minute,
            'next_goal_probability': self.next_goal_probability,
            'attack_potential': self.attack_potential,
            'match_minute': self.match_minute,
            'current_score': self.current_score,
            'xg_total': self.xg_total
        }

@dataclass
class Alert:
    """Модель оповещения"""
    match_id: int
    timestamp: datetime
    type: str
    text: str
    probability: Optional[float] = None
    data: Dict = field(default_factory=dict)