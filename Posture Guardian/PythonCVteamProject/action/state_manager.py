# state_manager.py
# 목적: 자세 모니터링 과정에서 발생하는 상태 변수와 타이머, 지속 시간 타이머를 관리
# Workflow: StateManager 객체 생성 → reset()으로 상태 초기화 → main 루프에서 참조 및 갱신

import time

class StateManager:
    """자세 모니터링 상태 및 타이머 관리 클래스"""

    def __init__(self):
        # 객체 생성 시 모든 상태 초기화
        self.reset()

    def reset(self):
        """모든 상태 변수 초기화"""
        # Stage 1~3에서 사용하는 타이머 변수
        self.ok_start_time = None          # 올바른 자세 유지 시작 시간
        self.not_ok_start_time = None      # 잘못된 자세 감지 시작 시간
        self.palm_start_time = None        # 손바닥 제스처 시작 시간
        self.fist_start_time = None        # 주먹 제스처 시작 시간

        # 나쁜 자세 감지 타이머
        self.bad_neck_start_time = None    # 거북목 감지 시작 시간
        self.bad_lean_start_time = None    # 앞으로/뒤로 기울임 감지 시작 시간
        self.bad_slouch_start_time = None  # 구부정 감지 시작 시간

        # 나쁜 자세 지속 (유지) 시간 카운트 (누적 시간)
        self.neck_duration = 0
        self.lean_duration = 0 # 앞/뒤
        self.slouch_duration = 0 # 구부정..

        # 경고 발생 여부 플래그
        self.neck_warning_triggered = False
        self.lean_warning_triggered = False
        self.slouch_warning_triggered = False

    def reset_warnings(self):
        """경고 플래그만 초기화"""
        self.neck_warning_triggered = False
        self.lean_warning_triggered = False
        self.slouch_warning_triggered = False

    def reset_gestures(self):
        """제스처 관련 타이머 초기화"""
        self.palm_start_time = None
        self.fist_start_time = None

    def reset_duration(self):
        '''지속 시간 카운터 초기화'''
        self.neck_duration = 0
        self.lean_duration = 0
        self.slouch_duration = 0