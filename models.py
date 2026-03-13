# models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class Team:
    """Модель команды"""
    id: int
    name: str
    country_code: Optional[str] = None
    logo_url: Optional[str] = None

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
    
    @property
    def total_shots(self) -> int:
        """Общее количество ударов"""
        return self.shots_home + self.shots_away
    
    @property
    def total_shots_ontarget(self) -> int:
        """Общее количество ударов в створ"""
        return self.shots_ontarget_home + self.shots_ontarget_away
    
    @property
    def shots_accuracy(self) -> float:
        """Точность ударов в процентах"""
        if self.total_shots > 0:
            return (self.total_shots_ontarget / self.total_shots) * 100
        return 0
    
    @property
    def total_corners(self) -> int:
        """Общее количество угловых"""
        return self.corners_home + self.corners_away
    
    @property
    def total_dangerous_attacks(self) -> int:
        """Общее количество опасных атак"""
        return self.dangerous_attacks_home + self.dangerous_attacks_away
    
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
    
    @property
    def home_xg_formatted(self) -> str:
        return f"{self.home_xg:.2f}"
    
    @property
    def away_xg_formatted(self) -> str:
        return f"{self.away_xg:.2f}"
    
    @property
    def total_xg_formatted(self) -> str:
        return f"{self.total_xg:.2f}"
    
    def to_dict(self) -> Dict:
        return {
            'home_xg': self.home_xg,
            'away_xg': self.away_xg,
            'total_xg': self.total_xg,
            'shots': self.shots,
            'source': self.source,
            'understat_id': self.understat_id
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
            'xg_data': self.xg_data.to_dict() if self.xg_data else None
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
    
    def format_telegram_message(self, match: Match) -> str:
        """Форматирует сообщение для Telegram с ссылкой на букмекера"""
        
        # Ссылка на матч у букмекера (например, 1xBet, Bet365 и т.д.)
        # Здесь можно использовать любой букмекер. Я выбрал 1xBet как пример
        bookmaker_url = f"https://1xbet.com/en/line/football/{match.id}"
        
        lines = [
            f"⚽️ **{match.home_team.name} vs {match.away_team.name}**",
            f"⏱️ Минута: **{self.minute}'** | Счет: **{self.score}**",
            f"🔗 [Смотреть матч у букмекера]({bookmaker_url})",
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
        lines.append("")
        
        lines.append(f"📈 **Активность:** {self.activity_level}")
        lines.append(f"💬 {self.activity_description}")
        lines.append("")
        
        if self.has_signal and self.next_signal:
            signal = self.next_signal
            lines.append(f"⚽️ **СИГНАЛ НА ГОЛ!**")
            lines.append(f"   • Ожидаемое время: **~{signal.predicted_minute}'**")
            lines.append(f"   • Вероятность: **{signal.probability:.1f}%**")
            
            if signal.xg_data:
                lines.append(f"   • xG: **{signal.xg_data.total_xg_formatted}**")
            
            lines.append(f"   • {signal.description}")
            
            if signal.is_high_priority:
                lines.append("")
                lines.append("🚨 **ВЫСОКАЯ ВЕРОЯТНОСТЬ ГОЛА!**")
        else:
            lines.append("⏳ **Нет активных сигналов на гол**")
        
        lines.append("")
        lines.append(f"🔥 Атакующий потенциал: {self.attack_potential}")
        
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
            'xg_data': self.xg_data.to_dict() if self.xg_data else None
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