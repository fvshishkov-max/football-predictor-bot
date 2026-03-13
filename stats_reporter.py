# stats_reporter.py
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class StatsReporter:
    """Класс для сбора и отправки статистики прогнозов"""
    
    def __init__(self, telegram_bot, channel_id: str):
        self.telegram_bot = telegram_bot
        self.channel_id = channel_id
        self.signals_since_last_report = []
        self.last_report_time = datetime.now()
        self.report_interval = timedelta(hours=6)
        self.signals_per_report = 10
        
    def add_signal(self, signal_data: Dict):
        """Добавляет сигнал в статистику"""
        self.signals_since_last_report.append(signal_data)
        current_count = len(self.signals_since_last_report)
        logger.info(f"StatsReporter: добавлен сигнал, всего в очереди: {current_count}")

        if current_count >= self.signals_per_report:
            logger.info(f"StatsReporter: набрано {current_count} сигналов, отправляю отчёт")
            self.send_report()
    
    def send_report(self):
        """Отправляет статистику в Telegram"""
        if not self.signals_since_last_report:
            logger.debug("StatsReporter: нет сигналов для отчёта")
            return
        
        now = datetime.now()
        if now - self.last_report_time < self.report_interval:
            logger.debug(f"StatsReporter: слишком рано для отчета. Последний был {self.last_report_time}")
            return
        
        total_signals = len(self.signals_since_last_report)
        logger.info(f"StatsReporter: формирование отчёта по {total_signals} сигналам")
        
        avg_probability = sum(s['signal_probability'] for s in self.signals_since_last_report) / total_signals
        
        minutes = [s['signal_minute'] for s in self.signals_since_last_report]
        minute_ranges = {
            '1-15': len([m for m in minutes if m <= 15]),
            '16-30': len([m for m in minutes if 15 < m <= 30]),
            '31-45': len([m for m in minutes if 30 < m <= 45]),
            '46-60': len([m for m in minutes if 45 < m <= 60]),
            '61-75': len([m for m in minutes if 60 < m <= 75]),
            '76-90': len([m for m in minutes if 75 < m <= 90])
        }
        
        leagues = [s['league_name'] for s in self.signals_since_last_report if s.get('league_name')]
        league_counter = Counter(leagues)
        top_leagues = league_counter.most_common(5)
        
        report = (
            f"📊 **СТАТИСТИКА ПРОГНОЗОВ**\n\n"
            f"📈 Последние {total_signals} сигналов:\n"
            f"   • Средняя вероятность: **{avg_probability:.1f}%**\n"
            f"   • Макс. вероятность: **{max(s['signal_probability'] for s in self.signals_since_last_report):.1f}%**\n"
            f"   • Мин. вероятность: **{min(s['signal_probability'] for s in self.signals_since_last_report):.1f}%**\n\n"
            f"⏱️ **Распределение по минутам:**\n"
        )
        
        for range_name, count in minute_ranges.items():
            if count > 0:
                percentage = (count / total_signals) * 100
                report += f"   • {range_name}: {count} ({percentage:.1f}%)\n"
        
        if top_leagues:
            report += f"\n🏆 **Топ-5 лиг:**\n"
            for league, count in top_leagues:
                percentage = (count / total_signals) * 100
                report += f"   • {league}: {count} ({percentage:.1f}%)\n"
        
        report += f"\n📅 Отчет за период: {self.last_report_time.strftime('%d.%m %H:%M')} - {now.strftime('%d.%m %H:%M')}"
        
        try:
            self.telegram_bot.message_queue.put({
                'key': f"stats_report_{now.timestamp()}",
                'text': report
            })
            logger.info(f"✅ StatsReporter: отчёт отправлен ({total_signals} сигналов)")
            
            self.signals_since_last_report = []
            self.last_report_time = now
            
        except Exception as e:
            logger.error(f"❌ StatsReporter: ошибка отправки отчёта: {e}")
    
    def force_report(self):
        """Принудительная отправка отчета"""
        if self.signals_since_last_report:
            self.send_report()