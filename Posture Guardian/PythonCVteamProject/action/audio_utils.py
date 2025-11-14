# audio_utils.py
# 목적: 오디오 큐를 사용하여 경고음을 순차적으로 재생
# Workflow:
# 1. 프로그램 시작 시 오디오 재생 전용 스레드(_audio_worker) 1개 실행
# 2. play_alert()가 호출되면, 오디오 파일을 큐(audio_queue)에 추가
# 3. _audio_worker는 큐를 감시하다가, 파일이 들어오면 순서대로 재생

import threading
import queue
from playsound import playsound

# 오디오 재생 요청을 처리하기 위한 큐
audio_queue = queue.Queue()

def _audio_worker():
    """
    오디오 큐를 감시하고 순서대로 재생하는
    백그라운드 워커 스레드 함수
    """
    while True:
        # 큐에 작업(사운드 파일)이 들어올 때까지 대기
        sound_file = audio_queue.get()
        
        # 작업(사운드) 재생 (block=True)
        # 워커 스레드에서 실행되므로 메인 루프(영상 처리 등)는 멈추지 않음
        try:
            playsound(sound_file, block=True)
        except Exception as e:
            # [중요] playsound는 경로에 한글이 포함되어 있으면
            # Unicode 관련 에러가 발생할 수 있습니다.
            # (예: C:\Users\사용자\ -> C:\Users\User\)
            if 'Unicode' in str(e):
                print(f"🚨 [오디오 에러] 'playsound'는 한글 경로를 지원하지 않습니다!")
                print(f"   -> 경로: {sound_file}")
            else:
                print(f"🚨 [오디오 에러] {e}")
        
        # 작업 완료를 큐에 알림
        audio_queue.task_done()

# 프로그램 시작 시 오디오 워커 스레드를 1회만 실행
# (daemon=True는 메인 프로그램이 종료되면 이 스레드도 자동 종료)
threading.Thread(target=_audio_worker, daemon=True).start()


def play_alert(sound_file):
    """
    경고음 재생을 요청하는 함수.
    실제 재생은 하지 않고, 오디오 큐에 파일 경로를 추가합니다.
    """
    audio_queue.put(sound_file)