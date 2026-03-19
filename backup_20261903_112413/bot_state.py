# bot_state.py
import json
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

class BotState:
    """Класс для управления состоянием бота между перезапусками"""
    
    def __init__(self, state_file: str = 'bot_stats.json'):
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self) -> Dict:
        """Загружает состояние из файла"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки состояния: {e}")
        
        # Создаем новое состояние по умолчанию
        return {
            'sent_signals': [],  # list of signal keys
            'last_restart': datetime.now().isoformat(),
            'total_signals_sent': 0,
            'bot_version': '2.0'
        }
    
    def save_state(self):
        """Сохраняет состояние в файл"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {e}")
    
    def is_signal_sent(self, signal_key: str) -> bool:
        """Проверяет, был ли уже отправлен сигнал"""
        return signal_key in self.state['sent_signals']
    
    def add_sent_signal(self, signal_key: str):
        """Добавляет отправленный сигнал"""
        if signal_key not in self.state['sent_signals']:
            self.state['sent_signals'].append(signal_key)
            self.state['total_signals_sent'] += 1
            # Ограничиваем размер списка
            if len(self.state['sent_signals']) > 500:
                self.state['sent_signals'] = self.state['sent_signals'][-250:]
            self.save_state()