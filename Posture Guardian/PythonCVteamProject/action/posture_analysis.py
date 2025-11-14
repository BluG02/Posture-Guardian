# posture_analysis.py
# 목적: MediaPipe Pose 랜드마크를 이용해 자세 각도 계산
# Workflow: calculate_angle_2d()로 세 점의 각도를 구해 자세 판별에 활용

import numpy as np

def calculate_angle_2d(a, b, c):
    """세 랜드마크 좌표로 각도 계산"""
    try:
        p_a = np.array([a.x, a.y])
        p_b = np.array([b.x, b.y])
        p_c = np.array([c.x, c.y])
        ba = p_a - p_b
        bc = p_c - p_b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle_rad = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle_rad)
    except:
        return None