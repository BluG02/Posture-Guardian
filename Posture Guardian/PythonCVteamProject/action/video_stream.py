import cv2, time
from threading import Thread

class VideoStream:
    """웹캠/RTSP 스트림을 별도 스레드에서 읽어오는 클래스"""

    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        print("Connecting to stream...")

        # ✅ 카메라 초기화 재시도 로직 추가
        self.ret, self.frame = None, None
        for _ in range(10):  # 최대 10번 시도
            self.ret, self.frame = self.cap.read()
            if self.ret:
                break
            time.sleep(0.5)  # 잠시 대기 후 재시도

        self.stopped = False
        if not self.ret:
            print("🚨 ERROR: 카메라 연결 실패. 장치 번호(src) 확인 필요.")
            self.stopped = True

    def start(self):
        """스레드 시작"""
        if not self.stopped:
            Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        """프레임을 지속적으로 읽어오는 루프"""
        while True:
            if self.stopped:
                self.cap.release()
                return
            self.ret, self.frame = self.cap.read()

    def read(self):
        """현재 프레임 반환"""
        return self.ret, self.frame

    def stop(self):
        """스트리밍 종료"""
        self.stopped = True