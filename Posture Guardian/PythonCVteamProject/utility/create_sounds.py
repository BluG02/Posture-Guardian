import os
from gtts import gTTS
# 음성 파일 생성/테스트
# Google TTS 사용해서 한국어 음성 파일 자동 생성
# 프로젝트에 사용할 경고 음성 mp3로 미리 만들어서 data 폴더에 저장

print("경고 음성 파일 생성을 시작합니다...")

# 1. 거북목
tts_neck = gTTS(text="거북목입니다. 허리를 펴주세요.", lang='ko')
tts_neck.save("warning_neck.mp3")

# 2. 앞으로 기울임
tts_lean_f = gTTS(text="앞으로 기울었습니다.", lang='ko')
tts_lean_f.save("warning_lean_forward.mp3")

# 3. 뒤로 기댐
tts_lean_b = gTTS(text="뒤로 기대고 있습니다.", lang='ko')
tts_lean_b.save("warning_lean_back.mp3")

# 4. 구부정 (Slouching)
tts_slouch = gTTS(text="등이 굽었습니다.", lang='ko')
tts_slouch.save("warning_slouch.mp3")

print("✅ 음성 파일 4개 (warning_neck.mp3 등)가 성공적으로 생성되었습니다.")