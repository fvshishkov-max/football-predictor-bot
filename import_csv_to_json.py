# import_csv_to_json.py
"""
Импорт всех исторических данных из CSV в predictions.json
Запуск: python import_csv_to_json.py
"""

import os
import json
import csv
import glob
from datetime import datetime
from collections import defaultdict

def import_csv_to_json():
    """Импортирует все CSV файлы в единый predictions.json"""
    
    print("="*60)
    print("📁 ИМПОРТ CSV В PREDICTIONS.JSON")
    print("="*60)
    
    history_dir = 'data/history'
    csv_files = glob.glob(os.path.join(history_dir, '*.csv'))
    
    print(f"\n📊 Найдено CSV файлов: {len(csv_files)}")
    
    all_predictions = []
    total_records = 0
    
    # Проходим по всем CSV файлам
    for i, csv_file in enumerate(csv_files):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Пробуем прочитать как CSV
                reader = csv.DictReader(f)
                records = list(reader)
                
                if records:
                    total_records += len(records)
                    if i < 5:  # Показываем первые 5 файлов
                        print(f"\n  📄 {os.path.basename(csv_file)}: {len(records)} записей")
                        print(f"     Поля: {list(records[0].keys())}")
                    
                    # Добавляем записи
                    for record in records:
                        # Преобразуем в формат, совместимый с predictions.json
                        pred = {
                            'match_id': record.get('match_id', 0),
                            'home_team': record.get('home_team', 'Unknown'),
                            'away_team': record.get('away_team', 'Unknown'),
                            'goal_probability': float(record.get('goal_probability', 0.5)),
                            'confidence_level': record.get('confidence_level', 'MEDIUM'),
                            'minute': int(record.get('minute', 0)),
                            'timestamp': record.get('timestamp', datetime.now().isoformat()),
                            'was_correct': record.get('was_correct', 'false').lower() == 'true',
                            'signal': True if float(record.get('goal_probability', 0)) > 0.46 else None
                        }
                        all_predictions.append(pred)
                        
        except Exception as e:
            print(f"  ⚠️ Ошибка чтения {csv_file}: {e}")
    
    print(f"\n📊 Всего импортировано записей: {total_records}")
    print(f"📊 Уникальных предсказаний: {len(set(p.get('match_id', 0) for p in all_predictions))}")
    
    # Сортируем по времени
    all_predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Вычисляем статистику
    correct = sum(1 for p in all_predictions if p.get('was_correct', False))
    total = len(all_predictions)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Статистика по уверенности
    conf_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    for pred in all_predictions:
        conf = pred.get('confidence_level', 'UNKNOWN')
        was_correct = pred.get('was_correct', False)
        conf_stats[conf]['total'] += 1
        if was_correct:
            conf_stats[conf]['correct'] += 1
    
    # Формируем итоговый JSON
    output_data = {
        'predictions': all_predictions,
        'accuracy_stats': {
            'total_predictions': total,
            'correct_predictions': correct,
            'incorrect_predictions': total - correct,
            'accuracy_rate': correct / total if total > 0 else 0,
            'by_confidence': {k: v for k, v in conf_stats.items()},
            'last_updated': datetime.now().isoformat()
        },
        'thresholds': {
            'low': 0.15,
            'medium': 0.25,
            'high': 0.40,
            'very_high': 0.55
        },
        'min_signal_probability': 0.46
    }
    
    # Сохраняем
    output_file = 'data/predictions/predictions.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Сохранено в {output_file}")
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"  • Всего предсказаний: {total}")
    print(f"  • Сбылось: {correct}")
    print(f"  • Не сбылось: {total - correct}")
    print(f"  • Точность: {accuracy:.1f}%")
    
    print(f"\n📊 ПО УРОВНЯМ УВЕРЕННОСТИ:")
    for conf, data in conf_stats.items():
        conf_acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        print(f"  • {conf}: {data['total']} прогнозов, точность {conf_acc:.1f}%")
    
    return output_data

if __name__ == "__main__":
    result = import_csv_to_json()