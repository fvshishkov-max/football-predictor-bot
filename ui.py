# ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import List, Dict, Set, Callable, Optional
import config
from models import Match, Prediction

class FootballAppUI:
    """Пользовательский интерфейс приложения"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ AI Football Predictor - LIVE сигналы голов")
        self.root.geometry("1400x800")
        self.root.configure(bg=config.COLORS['bg'])
        
        # Переменные
        self.auto_send_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="🔴 OFFLINE")
        
        # Callbacks
        self.on_refresh_callback = None
        self.on_analyze_callback = None
        self.on_track_callback = None
        self.on_send_callback = None
        self.on_show_all_callback = None
        self.on_auto_send_toggle = None
        
        # Храним ссылки на виджеты
        self.match_widgets = {}
        self.selected_match = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=config.COLORS['bg'], height=50)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Заголовок
        title = tk.Label(
            top_frame, 
            text="⚽ AI Football Predictor - LIVE сигналы голов", 
            font=("Arial", 16, "bold"),
            fg=config.COLORS['accent'],
            bg=config.COLORS['bg']
        )
        title.pack(side=tk.LEFT, padx=10)
        
        # Статус
        self.status_label = tk.Label(
            top_frame,
            textvariable=self.status_var,
            font=("Arial", 12),
            fg="red",
            bg=config.COLORS['bg']
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Кнопка обновления
        refresh_btn = tk.Button(
            top_frame,
            text="🔄 Обновить",
            command=self._on_refresh,
            bg=config.COLORS['accent'],
            fg=config.COLORS['fg'],
            font=("Arial", 10, "bold"),
            padx=15
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка все матчи
        all_matches_btn = tk.Button(
            top_frame,
            text="📅 Все матчи",
            command=self._on_show_all,
            bg=config.COLORS['info'],
            fg=config.COLORS['bg'],
            font=("Arial", 10, "bold"),
            padx=15
        )
        all_matches_btn.pack(side=tk.RIGHT, padx=5)
        
        # Чекбокс автоотправки
        auto_send_cb = tk.Checkbutton(
            top_frame,
            text="🤖 Автоотправка",
            variable=self.auto_send_var,
            command=self._on_auto_send_toggle,
            bg=config.COLORS['bg'],
            fg=config.COLORS['fg'],
            selectcolor=config.COLORS['bg'],
            font=("Arial", 10)
        )
        auto_send_cb.pack(side=tk.RIGHT, padx=10)
        
        # Основной контент
        main_frame = tk.Frame(self.root, bg=config.COLORS['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - список матчей
        left_frame = tk.Frame(main_frame, bg=config.COLORS['card_bg'], width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Заголовок списка матчей
        matches_title = tk.Label(
            left_frame,
            text="🔴 LIVE МАТЧИ",
            font=("Arial", 14, "bold"),
            fg=config.COLORS['live'],
            bg=config.COLORS['card_bg']
        )
        matches_title.pack(pady=10)
        
        # Canvas для скроллинга
        canvas = tk.Canvas(left_frame, bg=config.COLORS['card_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=config.COLORS['card_bg'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Правая панель
        right_frame = tk.Frame(main_frame, bg=config.COLORS['bg'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Верхняя часть - анализ
        self.analysis_frame = tk.Frame(
            right_frame, 
            bg=config.COLORS['card_bg'],
            height=400
        )
        self.analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.analysis_frame.pack_propagate(False)
        
        # Заголовок анализа
        analysis_title = tk.Label(
            self.analysis_frame,
            text="📊 АНАЛИЗ МАТЧА",
            font=("Arial", 14, "bold"),
            fg=config.COLORS['info'],
            bg=config.COLORS['card_bg']
        )
        analysis_title.pack(pady=10)
        
        # Текст анализа
        self.analysis_text = scrolledtext.ScrolledText(
            self.analysis_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg=config.COLORS['bg'],
            fg=config.COLORS['fg'],
            height=15
        )
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Кнопки под анализом
        buttons_frame = tk.Frame(self.analysis_frame, bg=config.COLORS['card_bg'])
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.track_btn = tk.Button(
            buttons_frame,
            text="🔔 Отслеживать",
            command=self._on_track,
            bg=config.COLORS['accent'],
            fg=config.COLORS['fg'],
            state=tk.DISABLED,
            width=15
        )
        self.track_btn.pack(side=tk.LEFT, padx=2)
        
        self.send_btn = tk.Button(
            buttons_frame,
            text="📤 Отправить сигнал",
            command=self._on_send,
            bg=config.COLORS['success'],
            fg=config.COLORS['fg'],
            state=tk.DISABLED,
            width=15
        )
        self.send_btn.pack(side=tk.LEFT, padx=2)
        
        # Нижняя часть - оповещения и статистика
        bottom_frame = tk.Frame(right_frame, bg=config.COLORS['bg'], height=250)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        bottom_frame.pack_propagate(False)
        
        # Оповещения
        alerts_frame = tk.Frame(bottom_frame, bg=config.COLORS['card_bg'])
        alerts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        alerts_title = tk.Label(
            alerts_frame,
            text="⚠️ ОПОВЕЩЕНИЯ",
            font=("Arial", 12, "bold"),
            fg=config.COLORS['warning'],
            bg=config.COLORS['card_bg']
        )
        alerts_title.pack(pady=5)
        
        self.alerts_text = scrolledtext.ScrolledText(
            alerts_frame,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg=config.COLORS['bg'],
            fg=config.COLORS['fg'],
            height=8
        )
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Статистика
        stats_frame = tk.Frame(bottom_frame, bg=config.COLORS['card_bg'])
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        stats_title = tk.Label(
            stats_frame,
            text="📈 СТАТИСТИКА МОДЕЛИ",
            font=("Arial", 12, "bold"),
            fg=config.COLORS['success'],
            bg=config.COLORS['card_bg']
        )
        stats_title.pack(pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg=config.COLORS['bg'],
            fg=config.COLORS['fg'],
            height=8
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Нижняя панель
        bottom_bar = tk.Frame(self.root, bg=config.COLORS['card_bg'], height=30)
        bottom_bar.pack(fill=tk.X, padx=10, pady=5)
        
        self.footer_label = tk.Label(
            bottom_bar,
            text="Готов к работе",
            font=("Arial", 9),
            fg=config.COLORS['fg'],
            bg=config.COLORS['card_bg']
        )
        self.footer_label.pack(side=tk.LEFT, padx=10)
    
    def update_matches(self, matches: List[Match], predictions: Dict[int, Prediction], 
                      selected_matches: Set[int], alerts: Dict[int, List] = None):
        """Обновляет список матчей с прогнозами"""
        # Очищаем старые виджеты
        for widget in self.match_widgets.values():
            widget.destroy()
        self.match_widgets.clear()
        
        # Сортируем матчи: LIVE первые
        live_matches = [m for m in matches if m.is_live]
        other_matches = [m for m in matches if not m.is_live]
        sorted_matches = live_matches + other_matches
        
        for match in sorted_matches[:20]:
            self._create_match_widget(
                match, 
                predictions.get(match.id), 
                match.id in selected_matches,
                alerts and match.id in alerts if alerts else False
            )
    
    def _create_match_widget(self, match: Match, prediction: Optional[Prediction], 
                            is_selected: bool, has_alerts: bool):
        """Создает виджет для одного матча"""
        frame = tk.Frame(
            self.scrollable_frame,
            bg=config.COLORS['card_bg'],
            relief=tk.RAISED,
            bd=1
        )
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Статус
        if match.is_live:
            status_text = f"🔴 {match.minute if match.minute else '?'}'"
            status_color = config.COLORS['live']
        else:
            status_text = "⏳ Скоро"
            status_color = config.COLORS['info']
        
        status_label = tk.Label(
            frame,
            text=status_text,
            font=("Arial", 8, "bold"),
            fg=status_color,
            bg=config.COLORS['card_bg']
        )
        status_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Название матча
        text = f"{match.home_team.name} vs {match.away_team.name}"
        if match.is_live:
            text += f" [{match.score}]"
        
        match_label = tk.Label(
            frame,
            text=text,
            font=("Arial", 10, "bold"),
            fg=config.COLORS['fg'],
            bg=config.COLORS['card_bg'],
            cursor="hand2"
        )
        match_label.pack(anchor=tk.W, padx=5)
        match_label.bind("<Button-1>", lambda e, m=match: self._on_match_click(m))
        
        # Индикаторы
        indicators_frame = tk.Frame(frame, bg=config.COLORS['card_bg'])
        indicators_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        if prediction and prediction.next_goal_minute:
            # Прогноз следующего гола
            goal_text = f"⚽ ~{prediction.next_goal_minute}' ({prediction.next_goal_probability:.0f}%)"
            goal_color = config.COLORS['profit_high'] if prediction.next_goal_probability > 70 else config.COLORS['info']
            
            goal_label = tk.Label(
                indicators_frame,
                text=goal_text,
                font=("Arial", 8),
                fg=goal_color,
                bg=config.COLORS['card_bg']
            )
            goal_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Статистика ударов
        if prediction and prediction.shots_stats:
            total_shots = prediction.shots_stats.get('total', 0)
            if total_shots > 0:
                shots_text = f"📊 {total_shots} уд."
                shots_label = tk.Label(
                    indicators_frame,
                    text=shots_text,
                    font=("Arial", 8),
                    fg=config.COLORS['info'],
                    bg=config.COLORS['card_bg']
                )
                shots_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Индикатор отслеживания
        if is_selected:
            track_label = tk.Label(
                indicators_frame,
                text="🔔",
                font=("Arial", 10),
                fg=config.COLORS['selected'],
                bg=config.COLORS['card_bg']
            )
            track_label.pack(side=tk.RIGHT, padx=2)
        
        # Индикатор оповещений
        if has_alerts:
            alert_label = tk.Label(
                indicators_frame,
                text="⚠️",
                font=("Arial", 10),
                fg=config.COLORS['warning'],
                bg=config.COLORS['card_bg']
            )
            alert_label.pack(side=tk.RIGHT, padx=2)
        
        self.match_widgets[match.id] = frame
    
    def _on_match_click(self, match):
        """Обработчик клика по матчу"""
        self.selected_match = match
        
        # Подсвечиваем выбранный матч
        for m_id, widget in self.match_widgets.items():
            if m_id == match.id:
                widget.configure(bg=config.COLORS['selected'])
            else:
                widget.configure(bg=config.COLORS['card_bg'])
        
        # Активируем кнопки
        self.track_btn.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        
        if self.on_analyze_callback:
            self.on_analyze_callback(match)
    
    def update_analysis(self, text: str):
        """Обновляет текст анализа"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, text)
    
    def update_alerts(self, alerts: List[Dict]):
        """Обновляет список оповещений"""
        self.alerts_text.delete(1.0, tk.END)
        for alert in alerts[-10:]:
            time_str = alert['timestamp'][11:19] if len(alert['timestamp']) > 19 else alert['timestamp']
            self.alerts_text.insert(tk.END, f"[{time_str}] {alert['text']}\n")
    
    # ui.py (фрагмент метода update_stats)
    
    def update_stats(self, stats: Dict):
        """Обновляет статистику модели"""
        self.stats_text.delete(1.0, tk.END)
        
        if stats:
            text = (
                f"Всего сигналов: {stats.get('total_predictions', 0)}\n"
                f"Точность: {stats.get('accuracy_rate', 0):.1f}%\n"
                f"Прогнозы голов: {stats.get('goals_predictions', 0)}\n"
                f"Ударов на гол: {stats.get('shots_per_goal', 9.5):.1f}\n"
                f"В створ на гол: {stats.get('ontarget_per_goal', 3.8):.1f}\n\n"
                f"⚙️ ПОРОГИ ПО ТАЙМАМ:\n"
            )
            
            thresholds = stats.get('thresholds', {})
            for time_min, thr in thresholds.items():
                text += f"   • до {time_min}': {thr*100:.0f}%\n"
            
            text += f"\n⚖️ ВЕСА МОДЕЛИ:\n"
            weights = stats.get('weights', {})
            for key, weight in weights.items():
                text += f"   • {key}: {weight*100:.0f}%\n"
        else:
            text = "Нет данных"
        
        self.stats_text.insert(1.0, text)
    
    def update_footer(self):
        """Обновляет нижнюю панель"""
        now = datetime.now().strftime("%H:%M:%S")
        self.footer_label.config(text=f"Последнее обновление: {now}")
    
    def set_status(self, text: str, color: str):
        """Устанавливает статус"""
        self.status_var.set(text)
        self.status_label.config(fg=color)
    
    def set_match_title(self, title: str):
        """Устанавливает заголовок матча в анализе"""
        for widget in self.analysis_frame.winfo_children():
            if isinstance(widget, tk.Label) and "АНАЛИЗ МАТЧА" in widget.cget("text"):
                widget.config(text=f"📊 {title}")
    
    def _on_refresh(self):
        """Обработчик кнопки обновления"""
        if self.on_refresh_callback:
            self.on_refresh_callback()
    
    def _on_show_all(self):
        """Обработчик кнопки все матчи"""
        if self.on_show_all_callback:
            self.on_show_all_callback()
    
    def _on_track(self):
        """Обработчик кнопки отслеживания"""
        if self.on_track_callback and self.selected_match:
            self.on_track_callback(self.selected_match)
    
    def _on_send(self):
        """Обработчик кнопки отправки"""
        if self.on_send_callback:
            self.on_send_callback()
    
    def _on_auto_send_toggle(self):
        """Обработчик чекбокса автоотправки"""
        if self.on_auto_send_toggle:
            self.on_auto_send_toggle(self.auto_send_var.get())