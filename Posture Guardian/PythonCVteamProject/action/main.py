# main.py
# 목적: 전체 프로그램 실행 로직 (카메라 연결 → 포즈 분석 → 제스처 인식 → 상태 머신 → 경고/로그 기록 → UI 출력)
# Workflow: VideoStream으로 프레임 읽기 → MediaPipe Pose/Hands 처리 → posture/gesture 분석 → StateManager로 상태 관리 → logger/audio_utils 호출
import warnings
warnings.filterwarnings("ignore") # 라이브러리 내부 경고문 무시 (출력하지 않음)
import cv2, time, numpy as np
import mediapipe as mp
from state_manager import StateManager
from PIL import ImageFont, ImageDraw, Image

# === 모듈 import ===
# 명시 호출 (Pylance 인식 문제)
from config import (
    POSE_MIN_DETECTION_CONFIDENCE,
    POSE_MIN_TRACKING_CONFIDENCE,
    HANDS_MAX_NUM_HANDS,
    HANDS_MIN_DETECTION_CONFIDENCE,
    HANDS_MIN_TRACKING_CONFIDENCE,
    SOUND_NECK,
    SOUND_LEAN_FORWARD,
    SOUND_LEAN_BACK,
    SOUND_SLOUCH,
    STRETCH_INTERVAL_SEC,
    STRETCH_ALERT_DURATION_SEC,
)
from config import * # posture_log.csv, mp3 경로, confidence 값 불러오기
from video_stream import VideoStream
from gesture_utils import is_victory, is_palm
from posture_analysis import calculate_angle_2d
from logger import setup_log_file, log_event
from audio_utils import play_alert
from state_manager import StateManager


# === 1. 초기화 ===

username = ""
password = ""
ip_address = ""
# (성능 최적화) 저해상도 스트림(stream2) 사용 권장
rtsp_url = f"rtsp://{username}:{password}@{ip_address}:554/stream2" 

setup_log_file()
cap = VideoStream(rtsp_url).start() 

print("✅ Camera stream successfully connected.")
print("   ('q' key to quit.)")

# MediaPipe 모델 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=POSE_MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=POSE_MIN_TRACKING_CONFIDENCE
)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=HANDS_MAX_NUM_HANDS,
    min_detection_confidence=HANDS_MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=HANDS_MIN_TRACKING_CONFIDENCE
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

state = StateManager()
current_stage = 1
FPS = 30

# --- 스트레칭 알림 타이머 초기화 ---
stretch_last_time = time.time()
stretch_alert_until = 0.0

stretch_alert_until = 0.0

# === [추가] 한글 폰트 로드 (PIL) ===
font_path = "c:/Windows/Fonts/malgun.ttf" # 윈도우 맑은 고딕
try:
    # 폰트 크기는 0.7 폰트 스케일과 비슷하게 20~25pt로 설정
    font = ImageFont.truetype(font_path, 25)
    print(f"✅ Korean font '{font_path}' loaded.")
except IOError:
    print(f"🚨 ERROR: Font not found at '{font_path}'.")
    print("-> Please check font path. Using default (broken) font.")
    font = None # 폰트 로드 실패

# === [추가] PIL로 텍스트 그리는 헬퍼 함수 ===
def draw_text_with_pil(img, text, position, text_color_bgr):
    """
    OpenCV 이미지를 받아 PIL로 변환 후 한글 텍스트를 그리고
    다시 OpenCV 이미지로 변환하여 반환합니다.
    """
    if font is None: # 폰트 로드 실패 시, 원래 OpenCV 함수 사용
        cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color_bgr, 2)
        return img

    # 1. OpenCV BGR 이미지를 RGB PIL 이미지로 변환
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    # 2. Draw 객체 생성
    draw = ImageDraw.Draw(img_pil)
    
    # 3. BGR 색상을 RGB로 변환 (PIL은 RGB 사용)
    text_color_rgb = (text_color_bgr[2], text_color_bgr[1], text_color_bgr[0])
    
    # 4. 텍스트 그리기 (폰트가 없으면 기본 폰트 사용)
    if font:
        draw.text(position, text, font=font, fill=text_color_rgb)
    else:
        draw.text(position, text, fill=text_color_rgb) # 기본 폰트
    
    # 5. PIL RGB 이미지를 다시 BGR OpenCV 이미지로 변환
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_cv

# === 2. 메인 루프 ===
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("- Waiting for frame...")
        time.sleep(0.5)
        continue

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # === [수정] 포즈 감지 (상세 가이드 추가) ===
    # (원본 코드의 상세 가이드 로직으로 복원)
    pose_results = pose.process(image_rgb)
    current_pose_ok = False # 기본값 초기화
    adjustment_messages = [] # 카메라 위치 안내 메세지 초기화
    landmarks = None # 랜드마크 초기화

    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        try: # try-except로 랜드마크 접근 보호
            nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

            # 랜드마크가 화면에 잘 보이는지 (visibility) 확인
            if all(lm.visibility > 0.7 for lm in [nose, left_shoulder, right_shoulder, left_hip, right_hip]):
                
                # 1. [복원] 중앙 정렬
                shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
                if not (0.5 - CENTER_TOLERANCE < shoulder_center_x < 0.5 + CENTER_TOLERANCE):
                    adj_msg = "RIGHT" if shoulder_center_x < 0.5 else "LEFT"
                    adjustment_messages.append(f"[ADJUST] Please move {adj_msg}")
                
                # 2. [복원] 상하/거리 정렬
                if nose.y < HEAD_ROOM_Y:
                    adjustment_messages.append("[ADJUST] Too close (move DOWN/BACK)")
                elif (left_hip.y > HIP_ROOM_Y or right_hip.y > HIP_ROOM_Y):
                    adjustment_messages.append("[ADJUST] Too far (move UP/CLOSER)")
                
                # 3. [복원] 모든 조정 메시지가 없으면 -> 자세 OK
                if not adjustment_messages:
                    current_pose_ok = True
            
            else: 
                adjustment_messages.append("[ERROR] Body not fully visible.")
        except Exception as e:
            adjustment_messages.append("[ERROR] Landmarks not fully detected.")
    else:
        adjustment_messages.append("[GUIDE] Please stand in front of the camera.")

    # 손 제스처 감지
    detected_gesture = None
    if current_stage in [2, 3]:
        hand_results = hands.process(image_rgb)
        if hand_results.multi_hand_landmarks:
            hand_landmarks = hand_results.multi_hand_landmarks[0]
            if is_palm(hand_landmarks):
                detected_gesture = "PALM"
            elif is_victory(hand_landmarks):
                detected_gesture = "VICTORY"
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

    # === Stage 로직 ===
    display_messages = []
    if current_stage == 1:
        # Stage 1: 카메라 세팅 (10초 유지)
        if current_pose_ok:
            if state.ok_start_time is None:
                state.ok_start_time = time.time()
            elapsed = time.time() - state.ok_start_time
            if elapsed >= HOLD_DURATION:
                current_stage = 2
                state.reset()
                display_messages = ["[ STAGE 2 ] Show Palm to START"]
            else:
                display_messages.append(f"[ OK ] Hold for {HOLD_DURATION - elapsed:.1f}s")
        else:
            state.ok_start_time = None
            display_messages = adjustment_messages # [수정] 상세 가이드 메시지 표시

    elif current_stage == 2:
        # Stage 2: 손바닥 제스처 대기 (3초 유지)
        display_messages = ["[ STAGE 2 ] Show Palm to START"]
        if detected_gesture == "PALM":
            if state.palm_start_time is None:
                state.palm_start_time = time.time()
            elapsed = time.time() - state.palm_start_time
            if elapsed >= GESTURE_HOLD_DURATION:
                current_stage = 3
                state.reset()
                display_messages = ["[ STAGE 3 ] Monitoring STARTED!"]
            else:
                display_messages.append(f"[ GESTURE ] Hold Palm {GESTURE_HOLD_DURATION - elapsed:.1f}s")
        else:
            state.palm_start_time = None

    elif current_stage == 3:
        # Stage 3: 모니터링 (자세 분석 + 브이 제스처로 종료)
        display_messages = ["[ STAGE 3 ] Monitoring... (Show 브이 Victory to STOP)"]

        if landmarks: # 자세 감지가 안 돼서 current_pose_ok 삭제
            # --- 거북목 감지 ---
            try: # [수정] 랜드마크 접근 보호
                ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
                shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                neck_angle = calculate_angle_2d(ear, shoulder, hip)

                if neck_angle and neck_angle < NECK_ANGLE_THRESHOLD:
                    if state.bad_neck_start_time is None:
                        state.bad_neck_start_time = time.time()
                    
                    # 나쁜 자세 지속 시간 (거북목)
                    state.neck_duration +=1
                    neck_duration_sec = state.neck_duration / FPS

                    elapsed = time.time() - state.bad_neck_start_time
                    if elapsed > BAD_POSTURE_DURATION:
                        display_messages.append(f"[WARNING] Turtle Neck! ({neck_angle:.0f}deg, {elapsed:.1f}s)")
                        if not state.neck_warning_triggered:
                            log_event("Turtle_Neck", neck_angle)
                            state.neck_warning_triggered = True
                            print(f"Neck angle  : {neck_angle:.1f}   (Held {neck_duration_sec:.1f}s)")
                            play_alert(SOUND_NECK)
                else:
                    state.bad_neck_start_time = None
                    state.neck_warning_triggered = False

                # --- 허리 기울임 감지 ---
                dy = -(shoulder.y - hip.y)
                dx = shoulder.x - hip.x
                lean_angle = np.degrees(np.arctan2(dy, dx))
                if not (LEAN_ANGLE_THRESHOLD_LOW < lean_angle < LEAN_ANGLE_THRESHOLD_HIGH):
                    if state.bad_lean_start_time is None:
                        state.bad_lean_start_time = time.time()

                    # 나쁜 자세 지속 시간 (기댄 자세 앞/뒤)
                    state.lean_duration +=1
                    lean_duration_sec = state.lean_duration / FPS

                    elapsed = time.time() - state.bad_lean_start_time
                    if elapsed > BAD_POSTURE_DURATION:
                        if lean_angle > LEAN_ANGLE_THRESHOLD_HIGH:
                            msg = "Leaning Forward!"
                            sound = SOUND_LEAN_FORWARD
                        else:
                            msg = "Leaning Back!"
                            sound = SOUND_LEAN_BACK
                        display_messages.append(f"[WARNING] {msg} ({lean_angle:.0f} deg, {elapsed: .1f}s)")
                        if not state.lean_warning_triggered:
                            log_event("Leaning", lean_angle)
                            state.lean_warning_triggered = True
                            print(f"Lean angle  : {lean_angle:.1f}   (Held {lean_duration_sec:.1f}s)")
                            play_alert(sound)
                else:
                    state.bad_lean_start_time = None
                    state.lean_warning_triggered = False

                # --- 구부정 감지 ---
                torso_h = abs(shoulder.x - hip.x)
                torso_v = abs(shoulder.y - hip.y)
                if torso_v > 0.01:
                    slouch_ratio = torso_h / torso_v
                    if slouch_ratio > SLOUCH_RATIO_THRESHOLD:
                        if state.bad_slouch_start_time is None:
                            state.bad_slouch_start_time = time.time()

                        # 나쁜 자세 지속 시간 (구부정..)
                        state.slouch_duration +=1
                        slouch_duration_sec = state.slouch_duration / FPS

                        elapsed = time.time() - state.bad_slouch_start_time
                        if elapsed > BAD_POSTURE_DURATION:
                            display_messages.append(f"[WARNING] Slouching! (ratio={slouch_ratio:.2f}, {elapsed: .1f}s)")
                            if not state.slouch_warning_triggered:
                                log_event("Slouching", slouch_ratio)
                                state.slouch_warning_triggered = True
                                print(f"Slouch ratio: {slouch_ratio:.2f}   (Held {slouch_duration_sec:.2f}s)")
                                play_alert(SOUND_SLOUCH)
                    else:
                        state.bad_slouch_start_time = None
                        state.slouch_warning_triggered = False
            
            except Exception as e:
                # Stage 3에서 랜드마크 계산 중 오류 발생 시
                display_messages.append("[ERROR] Angle calculation failed.")
                
        # --- [스트레칭 리마인더: 테스트용 1분 주기] ---
        now = time.time()
        if now - stretch_last_time >= STRETCH_INTERVAL_SEC:
            stretch_last_time = now
            stretch_alert_until = now + STRETCH_ALERT_DURATION_SEC
            print("[STRETCH] It's time to stretch your body!")


        # --- 브이 제스처로 종료 ---
        if detected_gesture == "VICTORY":
            if state.fist_start_time is None:
                state.fist_start_time = time.time()
            elapsed = time.time() - state.fist_start_time
            if elapsed >= GESTURE_HOLD_DURATION:
                current_stage = 1
                state.reset()
                display_messages = ["[ RESET ] Monitoring stopped."]
            else:
                # ✅ [추가] 브이 제스처 카운트다운 메시지
                display_messages.append(f"[ GESTURE ] Hold Victory {GESTURE_HOLD_DURATION - elapsed:.1f}s")
        else:
            state.fist_start_time = None

    # === [신규] 공통 리셋 로직 (Safety Reset) ===
    # 2/3단계일 때, 자세가 30초 이상 이탈하면 1단계로 강제 리셋
    if current_stage == 2 or current_stage == 3:
        if not current_pose_ok:
            if state.not_ok_start_time is None: 
                state.not_ok_start_time = time.time()
            elapsed_not_ok = time.time() - state.not_ok_start_time
            remaining_time = RESET_DURATION - elapsed_not_ok
            
            if remaining_time <= 0:
                # 30초 이탈 -> 1단계로 리셋
                current_stage = 1
                state.reset() # StateManager로 모든 타이머 리셋
                display_messages = ["[ RESET ] Position lost. Returning to setup..."]
                # 스트레칭 타이머도 리셋
                stretch_last_time = time.time()
                stretch_alert_until = 0.0
            else:
                display_messages.append(f"[ WARNING ] Position lost. Reset in {remaining_time:.0f}s")
                # (중요) 이탈 사유를 보여주기 위해 adjustment_messages를 추가
                display_messages.extend(adjustment_messages) 
        else:
            # 자세가 정상이면 리셋 타이머 초기화
            if state.not_ok_start_time is not None: 
                state.not_ok_start_time = None

    # --- [스트레칭 알림 표시] ---
    if time.time() < stretch_alert_until:
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
        alpha = 0.5
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # [수정] 한글 메시지로 변경 및 PIL 함수 사용
        stretch_msg = "스트레칭 시간입니다!" 
        text_color_bgr = (255, 255, 255) # 흰색 (BGR)
        
        # (주의: PIL 폰트 기준점이 약간 달라서 (20, 50) -> (20, 40)으로 y좌표 조정)
        frame = draw_text_with_pil(frame, stretch_msg, (20, 40), text_color_bgr)
        
    # UI 메시지 출력
    # y_offset = 30  <- (이 변수는 PIL 헬퍼 함수를 쓰면 필요 없어짐)
    for i, msg in enumerate(display_messages):
        # [수정] 메시지 색상 변경 로직 추가 (이건 그대로 사용)
        color = (0, 255, 0) # 기본 녹색 (OK)
        if "ERROR" in msg or "GUIDE" in msg: color = (0, 0, 255) # 적색
        elif "ADJUST" in msg: color = (0, 165, 255) # 주황
        elif "WARNING" in msg or "RESET" in msg: color = (0, 69, 255) # 진한 주황
        elif "Hold" in msg: color = (255, 255, 0) # 청록색 (대기)

        # [수정] cv2.putText 대신 PIL 헬퍼 함수 사용
        # (주의: PIL은 이미지를 반환하므로 frame을 덮어써야 함)
        # (PIL 폰트 기준점이 약간 다르므로 y 좌표를 살짝 조정 (예: 25 + i * 35))
        frame = draw_text_with_pil(frame, msg, (20, 25 + i * 35), color)

    if pose_results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    cv2.imshow('Posture Guardian - Project (Voice Enabled)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# === 종료 처리 ===
print("Shutting down...")
pose.close()
hands.close()
cap.stop()
cv2.destroyAllWindows()