import cv2
import mediapipe as mp
import numpy as np
import time
import math
from threading import Thread

# ... (VideoStream 클래스, calculate_angle_2d 함수 동일) ...
class VideoStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        print("Connecting to stream...")
        time.sleep(1.0) 
        (self.ret, self.frame) = self.cap.read()
        self.stopped = False
        if not self.ret:
             print("🚨 ERROR: Stream connection failed.")
             self.stopped = True
    def start(self):
        if not self.stopped:
            Thread(target=self.update, args=(), daemon=True).start()
        return self
    def update(self):
        while True:
            if self.stopped: self.cap.release(); return
            (self.ret, self.frame) = self.cap.read()
    def read(self):
        return self.ret, self.frame
    def stop(self):
        self.stopped = True
def calculate_angle_2d(a, b, c):
    try:
        p_a = np.array([a.x, a.y])
        p_b = np.array([b.x, b.y])
        p_c = np.array([c.x, c.y])
        ba = p_a - p_b
        bc = p_c - p_b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle_rad = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle_rad)
    except Exception as e:
        return None
# -----------------------------------------------

# --- MediaPipe 포즈 모델 초기화 ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- RTSP 실시간 스트림 소스 ---
username = ""
password = ""
ip_address = ""
rtsp_url = f"rtsp://{username}:{password}@{ip_address}:554/stream2" 
cap = VideoStream(rtsp_url).start()
# -----------------------------------------------

print("✅ Angle Debugger (RTSP Mode) - Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        time.sleep(0.5); continue
    
    frame = cv2.resize(frame, (960, 540))
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    pose_results = pose.process(image_rgb)
    
    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        frame_h, frame_w, _ = frame.shape
        
        try:
            ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            
            # --- 1. 거북목 각도 (Neck) ---
            current_neck_angle = calculate_angle_2d(ear, shoulder, hip)
            
            # --- 2. 기울임 각도 (Lean) ---
            dy = -(shoulder.y - hip.y) 
            dx = shoulder.x - hip.x
            current_lean_angle = np.degrees(np.arctan2(dy, dx))
            
            # --- 3. (★추가★) 구부정 비율 (Slouch Ratio) ---
            current_slouch_ratio = None
            torso_h_dist = abs(shoulder.x - hip.x)
            torso_v_dist = abs(shoulder.y - hip.y)
            if torso_v_dist > 0.01:
                current_slouch_ratio = torso_h_dist / torso_v_dist
            # -----------------------------------------------

            # --- 각도를 화면에 실시간 표시 ---
            shoulder_px = (int(shoulder.x * frame_w), int(shoulder.y * frame_h))
            
            if current_neck_angle is not None:
                cv2.putText(frame, f"Neck: {current_neck_angle:.1f}", 
                            (shoulder_px[0] + 10, shoulder_px[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                            
            if current_lean_angle is not None:
                cv2.putText(frame, f"Lean: {current_lean_angle:.1f}", 
                            (shoulder_px[0] + 10, shoulder_px[1] + 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # (★추가★)
            if current_slouch_ratio is not None:
                color = (0, 0, 255) if current_slouch_ratio > 0.3 else (0, 255, 255) # 0.3 임계값 테스트
                cv2.putText(frame, f"Slouch Ratio: {current_slouch_ratio:.2f}", 
                            (shoulder_px[0] + 10, shoulder_px[1] + 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        except Exception as e:
            pass 

        mp_drawing.draw_landmarks(
            frame,
            pose_results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
    
    cv2.imshow('Angle Debugger (RTSP)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print("Shutting down stream...")
cap.stop() 
pose.close()
cv2.destroyAllWindows()