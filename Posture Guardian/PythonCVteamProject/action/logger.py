# logger.py
# 목적: CSV 파일에 이벤트 로그 기록
# Workflow: setup_log_file()로 초기화 → log_event()로 이벤트 기록

import csv
from datetime import datetime
from config import LOG_FILENAME

def setup_log_file():
    """CSV 로그 파일 초기화"""
    with open(LOG_FILENAME, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "event_type", "value"])

def log_event(event_type, value):
    """이벤트 로그 기록"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILENAME, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, event_type, round(value, 2)])