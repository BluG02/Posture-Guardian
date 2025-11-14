# config.py
# 목적: 프로젝트 전체에서 사용하는 설정값과 상수를 관리
# Workflow: 모든 모듈이 import하여 동일한 기준값을 참조

# 카메라 설정
CAMERA_INDEX = 0
FRAME_WIDTH = 960
FRAME_HEIGHT = 540

# Mediapipe 설정
POSE_MIN_DETECTION_CONFIDENCE = 0.5
POSE_MIN_TRACKING_CONFIDENCE = 0.5

HANDS_MAX_NUM_HANDS = 2
HANDS_MIN_DETECTION_CONFIDENCE = 0.7
HANDS_MIN_TRACKING_CONFIDENCE = 0.7


# 자세 판별 기준값
CENTER_TOLERANCE = 0.15
HEAD_ROOM_Y = 0.1
HIP_ROOM_Y = 0.85

# 타이머 설정
HOLD_DURATION = 5  #원래 10
RESET_DURATION = 10  #원래 30
GESTURE_HOLD_DURATION = 3
BAD_POSTURE_DURATION = 5

STRETCH_INTERVAL_SEC = 30
STRETCH_ALERT_DURATION_SEC = 5

# 각도/비율 기준
NECK_ANGLE_THRESHOLD = 150
LEAN_ANGLE_THRESHOLD_LOW = 85
LEAN_ANGLE_THRESHOLD_HIGH = 95
SLOUCH_RATIO_THRESHOLD = 0.09

# 로그 파일 이름
LOG_FILENAME = "PythonCVteamProject/posture_log.csv"

# === 음성 파일 경로 ===
SOUND_NECK = "PythonCVteamProject\data\warning_neck.mp3"
SOUND_LEAN_FORWARD = "PythonCVteamProject\data\warning_lean_forward.mp3"
SOUND_LEAN_BACK = "PythonCVteamProject\data\warning_lean_back.mp3"
SOUND_SLOUCH = "PythonCVteamProject\data\warning_slouch.mp3"

