# app.py
import tkinter as tk
import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
import json
import os
from queue import Queue

from api_client import SStatsClient
from predictor import Predictor
from telegram_bot import TelegramBot
from database import Database
from ui import FootballAppUI
from models import Match, LiveStats, MatchAnalysis, Prediction
from bot_state import BotState
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/football_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FootballApp:
    """Главный класс приложения с поддержкой async/await"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.ui = FootballAppUI(self.root)
        
        self.api_client = SStatsClient(
            api_key=config.SSTATS_API_KEY, 
            timezone=config.TIMEZONE,
            use_mock=config.USE_MOCK_DATA
        )
        self.predictor = Predictor()
        self.telegram = TelegramBot(config.BOT_TOKEN, config.CHANNEL_ID)
        self.db = Database()
        self.state = BotState()
        
        # Создаем event loop для асинхронных операций
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_loop, daemon=True)
        self.loop_thread.start()
        
        # Очередь для результатов из асинхронных задач
        self.result_queue = Queue()
        
        # Данные
        self.matches: List[Match] = []
        self.all_matches: List[Match] = []
        self.analyses: Dict[int, MatchAnalysis] = {}
        self.selected_matches: Set[int] = set()
        self.sent_signals: Set[str] = set()
        
        # Тайминг
        self.last_signal_time = 0
        self.signal_cooldown = 5
        self.update_in_progress = False
        self.stop_monitoring = False
        self.last_update_time = 0
        self.update_interval = 60  # Обновление каждые 60 секунд
        
        # Подключаем обработчики UI
        self.ui.on_refresh_callback = self.refresh_matches
        self.ui.on_analyze_callback = self.analyze_match
        self.ui.on_track_callback = self.toggle_tracking
        self.ui.on_send_callback = self.send_signal_to_telegram
        self.ui.on_show_all_callback = self.show_all_matches
        self.ui.on_auto_send_toggle = self.toggle_auto_send
        
        # Загружаем данные
        self.load_from_state()
        
        # Запускаем периодическое обновление UI результатами
        self.root.after(100, self._process_results)
        
        # Первое обновление
        self.root.after(100, self.refresh_matches)
        
        # Запускаем фоновый мониторинг
        self.start_background_monitoring()
        
        logger.info("✅ Приложение запущено")
        logger.info(f"📊 Статистика: сигналов {self.predictor.accuracy_stats['total_signals']}")
    
    def start_background_monitoring(self):
        """Запускает фоновый поток для автоматического обновления"""
        def monitor():
            while not self.stop_monitoring:
                try:
                    time.sleep(self.update_interval)
                    if not self.update_in_progress:
                        logger.info("🔄 Автоматическое обновление матчей...")
                        self.root.after(0, self.refresh_matches)
                except Exception as e:
                    logger.error(f"Ошибка в мониторинге: {e}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        logger.info(f"🔄 Фоновый мониторинг запущен (интервал: {self.update_interval}с)")
    
    def _start_loop(self):
        """Запускает event loop в отдельном потоке"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def _process_results(self):
        """Обрабатывает результаты из очереди и обновляет UI"""
        try:
            while not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                result_type = result.get('type')
                
                if result_type == 'update_ui':
                    self._update_ui_data(result.get('data', {}))
                elif result_type == 'analysis_result':
                    match_id = result.get('match_id')
                    analysis = result.get('analysis')
                    match = result.get('match')
                    if match_id and analysis and match:
                        self.analyses[match_id] = analysis
                        self._check_goal_signals(match, analysis)
                elif result_type == 'error':
                    logger.error(f"Ошибка: {result.get('error')}")
        except Exception as e:
            logger.error(f"Ошибка обработки результатов: {e}")
        finally:
            self.root.after(100, self._process_results)
    
    def _update_ui_data(self, data: Dict):
        if 'matches' in data:
            self.matches = data['matches']
        if 'all_matches' in data:
            self.all_matches = data['all_matches']
        self.ui.set_status("🟢 ONLINE", "green")
        self.update_ui()
    
    def load_from_state(self):
        self.sent_signals = set(self.state.state['sent_signals'])
        try:
            if os.path.exists('data/selected_matches.json'):
                with open('data/selected_matches.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.selected_matches = set(data.get('selected', []))
        except Exception as e:
            logger.error(f"Ошибка загрузки выбранных матчей: {e}")
    
    def analyze_match(self, match):
        self.ui.selected_match = match
        analysis = self.analyses.get(match.id)
        if analysis and isinstance(analysis, MatchAnalysis):
            text = analysis.format_telegram_message(match)
            self.ui.update_analysis(text)
        else:
            home_flag = self._get_flag_emoji(match.home_team.country_code)
            away_flag = self._get_flag_emoji(match.away_team.country_code)
            text = f"📊 ИНФОРМАЦИЯ О МАТЧЕ\n\n"
            text += f"{home_flag} {match.home_team.name} vs {away_flag} {match.away_team.name}\n"
            text += f"⚽ Счет: {match.score}\n"
            if match.minute:
                text += f"⏱️ Минута: {match.minute}'\n"
            text += f"🏆 Лига: {match.league_name}\n"
            text += f"\n🔄 Анализ еще не выполнен"
            self.ui.update_analysis(text)
    
    def refresh_matches(self):
        """Обновление списка матчей"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            logger.debug(f"Слишком частые обновления, пропускаем. Прошло: {current_time - self.last_update_time:.1f}с")
            return
        
        if self.update_in_progress:
            logger.debug("Обновление уже выполняется, пропускаем")
            return
        
        self.update_in_progress = True
        self.last_update_time = current_time
        self.ui.set_status("🟡 ЗАГРУЗКА...", "orange")
        
        def load():
            try:
                async def fetch_data():
                    tasks = [
                        self.api_client.get_live_matches(),
                        self.api_client.get_today_matches()
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    return results
                
                # Запускаем с таймаутом
                future = asyncio.run_coroutine_threadsafe(fetch_data(), self.loop)
                results = future.result(timeout=30)
                
                matches = results[0] if not isinstance(results[0], Exception) else []
                all_matches = results[1] if not isinstance(results[1], Exception) else []
                
                if isinstance(results[0], Exception):
                    logger.error(f"Ошибка получения LIVE матчей: {results[0]}")
                if isinstance(results[1], Exception):
                    logger.error(f"Ошибка получения всех матчей: {results[1]}")
                
                async def analyze_matches():
                    analyses_results = []
                    for match in matches:
                        try:
                            stats = await self.api_client.get_match_statistics(match.id)
                            if stats:
                                analysis = await self.predictor.analyze_live_match(match, stats)
                                analyses_results.append((match, analysis))
                        except Exception as e:
                            logger.error(f"Ошибка обработки матча {match.id}: {e}")
                    return analyses_results
                
                # Запускаем анализ с таймаутом
                if matches:
                    future_analysis = asyncio.run_coroutine_threadsafe(analyze_matches(), self.loop)
                    analyses_results = future_analysis.result(timeout=60)
                    
                    for match, analysis in analyses_results:
                        if analysis:
                            self.result_queue.put({
                                'type': 'analysis_result',
                                'match_id': match.id,
                                'match': match,
                                'analysis': analysis
                            })
                
                self.result_queue.put({
                    'type': 'update_ui',
                    'data': {
                        'matches': matches,
                        'all_matches': all_matches
                    }
                })
                
                logger.info(f"✅ Обновление завершено. Найдено LIVE матчей: {len(matches)}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки: {e}")
                self.root.after(0, lambda: self.ui.set_status("🔴 ОШИБКА", "red"))
            finally:
                self.update_in_progress = False
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _check_goal_signals(self, match: Match, analysis: MatchAnalysis):
        if not analysis.has_signal or not analysis.next_signal:
            return
        
        signal = analysis.next_signal
        signal_key = f"{match.id}_{signal.predicted_minute}"
        
        if self.state.is_signal_sent(signal_key):
            logger.debug(f"Сигнал {signal_key} уже был отправлен")
            return
        
        # Проверяем минимальную вероятность для отправки (50%)
        min_probability = self.predictor.params.get('min_send_probability', 50.0)
        if signal.probability < min_probability:
            logger.debug(f"Сигнал {signal_key} имеет низкую вероятность ({signal.probability:.1f}% < {min_probability}%)")
            return
        
        current_time = time.time()
        if current_time - self.last_signal_time < self.signal_cooldown:
            logger.debug(f"Cooldown: ждем {self.signal_cooldown - (current_time - self.last_signal_time):.1f}с")
            return
        
        if not self.ui.auto_send_var.get():
            logger.debug("Автоотправка выключена")
            return
        
        message = analysis.format_telegram_message(match)
        
        if self.telegram.send_goal_signal(match, analysis, message):
            self.state.add_sent_signal(signal_key)
            self.last_signal_time = current_time
            self.predictor.save_signal_to_history(match, signal)
            logger.info(f"✅ СИГНАЛ ОТПРАВЛЕН {match.id}: {match.home_team.name}-{match.away_team.name} "
                       f"~{signal.predicted_minute}' ({signal.probability:.1f}%)")
        else:
            logger.error(f"❌ Ошибка отправки сигнала {signal_key}")
    
    def show_all_matches(self):
        if not self.all_matches:
            self.ui.update_analysis("📅 Загружаю расписание...")
            self.refresh_matches()
            return
        
        live = [m for m in self.all_matches if m.is_live]
        scheduled = [m for m in self.all_matches if not m.is_live and not m.is_finished]
        finished = [m for m in self.all_matches if m.is_finished]
        
        text = f"📋 ВСЕ МАТЧИ НА СЕГОДНЯ ({len(self.all_matches)})\n\n"
        
        if live:
            text += f"🔴 LIVE ({len(live)}):\n"
            for m in live[:5]:
                home_flag = self._get_flag_emoji(m.home_team.country_code)
                away_flag = self._get_flag_emoji(m.away_team.country_code)
                text += f"   • {home_flag} {m.home_team.name} vs {away_flag} {m.away_team.name}"
                if m.minute:
                    text += f" ({m.minute}')"
                text += f" [{m.home_score}:{m.away_score}]\n"
            text += "\n"
        
        if scheduled:
            text += f"⏳ ПРЕДСТОЯЩИЕ ({len(scheduled)}):\n"
            for m in scheduled[:5]:
                home_flag = self._get_flag_emoji(m.home_team.country_code)
                away_flag = self._get_flag_emoji(m.away_team.country_code)
                text += f"   • {home_flag} {m.home_team.name} vs {away_flag} {m.away_team.name}\n"
            text += "\n"
        
        if finished:
            text += f"✅ ЗАВЕРШЕННЫЕ ({len(finished)}):\n"
            for m in finished[:5]:
                home_flag = self._get_flag_emoji(m.home_team.country_code)
                away_flag = self._get_flag_emoji(m.away_team.country_code)
                text += f"   • {home_flag} {m.home_team.name} {m.home_score}-{m.away_score} {away_flag} {m.away_team.name}\n"
        
        self.ui.update_analysis(text)
    
    def _get_flag_emoji(self, country_code: str) -> str:
        if not country_code:
            return "🌍"
        flags = {
            'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'eng': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
            'spain': '🇪🇸', 'esp': '🇪🇸',
            'italy': '🇮🇹', 'ita': '🇮🇹',
            'germany': '🇩🇪', 'ger': '🇩🇪',
            'france': '🇫🇷', 'fra': '🇫🇷',
            'netherlands': '🇳🇱', 'ned': '🇳🇱',
            'portugal': '🇵🇹', 'por': '🇵🇹',
            'turkey': '🇹🇷', 'tur': '🇹🇷',
            'russia': '🇷🇺', 'rus': '🇷🇺',
            'ukraine': '🇺🇦', 'ukr': '🇺🇦',
            'belgium': '🇧🇪', 'bel': '🇧🇪',
            'switzerland': '🇨🇭', 'sui': '🇨🇭',
            'austria': '🇦🇹', 'aut': '🇦🇹',
            'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'sco': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
            'wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'wal': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
            'usa': '🇺🇸', 'brazil': '🇧🇷', 'bra': '🇧🇷',
            'argentina': '🇦🇷', 'arg': '🇦🇷', 'japan': '🇯🇵', 'jpn': '🇯🇵',
        }
        return flags.get(country_code.lower(), '🌍')
    
    def update_ui(self):
        predictions = {}
        for match_id, analysis in self.analyses.items():
            if isinstance(analysis, MatchAnalysis):
                pred = Prediction(
                    match_id=match_id,
                    type='live',
                    timestamp=datetime.now(),
                    next_goal_minute=analysis.next_signal.predicted_minute if analysis.next_signal else None,
                    next_goal_probability=analysis.next_signal.probability if analysis.next_signal else 0,
                    attack_potential=analysis.attack_potential,
                    match_minute=analysis.minute,
                    current_score=analysis.score,
                    shots_stats=analysis.stats.to_dict().get('shots', {}),
                    possession_stats=analysis.stats.to_dict().get('possession', {})
                )
                predictions[match_id] = pred
        
        self.ui.update_matches(self.matches, predictions, self.selected_matches, {})
        self.ui.update_alerts(self.db.get_recent_alerts(10))
        
        stats = {
            'total_predictions': self.predictor.accuracy_stats['total_signals'],
            'accuracy_rate': self.predictor.accuracy_stats.get('accuracy_rate', 0),
            'goals_predictions': self.predictor.accuracy_stats['total_signals'],
            'goals_accuracy': self.predictor.accuracy_stats.get('accuracy_rate', 0),
            'shots_per_goal': self.predictor.params['shots_per_goal'],
            'ontarget_per_goal': self.predictor.params['ontarget_per_goal'],
            'threshold': self.predictor.params['probability_threshold'] * 100,
            'thresholds': self.predictor.thresholds,
            'weights': self.predictor.weights,
            'xg_accuracy': self.predictor.accuracy_stats.get('xg_accuracy', 0) * 100,
            'min_send_probability': self.predictor.params.get('min_send_probability', 50)
        }
        self.ui.update_stats(stats)
        self.ui.update_footer()
    
    def toggle_tracking(self, match):
        match_id = match.id
        if match_id in self.selected_matches:
            self.selected_matches.remove(match_id)
            logger.info(f"⏸️ Отслеживание матча {match_id} остановлено")
        else:
            self.selected_matches.add(match_id)
            logger.info(f"🔔 Начато отслеживание матча {match_id}")
        self.save_selected_matches()
        self.update_ui()
    
    def save_selected_matches(self):
        try:
            with open('data/selected_matches.json', 'w', encoding='utf-8') as f:
                json.dump({'selected': list(self.selected_matches)}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения выбранных матчей: {e}")
    
    def toggle_auto_send(self, enabled: bool):
        logger.info(f"🤖 Автоотправка сигналов {'включена' if enabled else 'выключена'}")
    
    def send_signal_to_telegram(self):
        if not hasattr(self.ui, 'selected_match') or not self.ui.selected_match:
            self.ui.update_analysis("❌ Сначала выберите матч")
            return
        
        match = self.ui.selected_match
        analysis = self.analyses.get(match.id)
        
        if not analysis:
            self.ui.update_analysis("❌ Анализ не найден")
            return
        
        if not analysis.has_signal or not analysis.next_signal:
            self.ui.update_analysis("❌ Нет активных сигналов на гол")
            return
        
        signal = analysis.next_signal
        message = analysis.format_telegram_message(match)
        
        if self.telegram.send_goal_signal(match, analysis, message):
            signal_key = f"{match.id}_{signal.predicted_minute}"
            self.state.add_sent_signal(signal_key)
            self.predictor.save_signal_to_history(match, signal)
            self.ui.update_analysis(f"✅ Сигнал отправлен в Telegram\n\n{message}")
        else:
            self.ui.update_analysis("❌ Ошибка отправки")
    
    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.stop_monitoring = True
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.predictor._save_all()
            asyncio.run_coroutine_threadsafe(self.predictor.close(), self.loop)


if __name__ == "__main__":
    app = FootballApp()
    app.run()