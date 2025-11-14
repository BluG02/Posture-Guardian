# gesture_utils.py
# 목적: MediaPipe Hands를 이용해 손 제스처(주먹, 손바닥) 인식
# Workflow: get_distance()로 거리 계산 → is_fist(), is_palm()으로 제스처 판별

import math
import mediapipe as mp

mp_hands = mp.solutions.hands

def get_distance(p1, p2):
    """두 랜드마크 사이의 거리 계산"""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

def is_victory(hand_landmarks):
    """검지와 중지가 펴져 있고, 나머지 손가락은 접혀 있으면 Victory(V)"""
    try:
        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP]

        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]

        # ✅ 판별 규칙
        index_extended = index_tip.y < index_pip.y
        middle_extended = middle_tip.y < middle_pip.y
        ring_folded = ring_tip.y > ring_pip.y
        pinky_folded = pinky_tip.y > pinky_pip.y
        return index_extended and middle_extended and ring_folded and pinky_folded
    except:
        return False

def is_palm(hand_landmarks):
    """손가락이 모두 펴져 있으면 손바닥"""
    try:
        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP]
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]

        return (
            get_distance(index_tip, wrist) > get_distance(index_pip, wrist) and
            get_distance(middle_tip, wrist) > get_distance(middle_pip, wrist) and
            get_distance(ring_tip, wrist) > get_distance(ring_pip, wrist) and
            get_distance(pinky_tip, wrist) > get_distance(pinky_pip, wrist)
        )
    except:
        return False