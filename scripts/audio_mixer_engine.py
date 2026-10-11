"""
Suno AI 생성 음원을 메인으로 사용하며,
API 키가 없을 때도 고음질 인스트루멘털 BGM + 보컬 하모닉스 및 마스터링을 적용하는 폴백 오디오 엔진
"""

import os
import glob
import random
import subprocess
from pydub import AudioSegment
from gtts import gTTS

def create_fallback_vocal_track(lyrics_text: str, output_path: str):
    """
    gTTS로 가사의 핵심 하이라이트 문장을 음성 합성 후 피치 시프트 및 코러스 적용
    """
    # 가사에서 대괄호 태그 제거하고 주요 텍스트 추출
    lines = [l.strip() for l in lyrics_text.split("\n") if l.strip() and not l.startswith("[")]
    sample_text = " ".join(lines[:4]) if lines else "꿈꾸던 어른이 되었나요"
    
    temp_tts = "temp/tts_raw.mp3"
    tts = gTTS(text=sample_text, lang="ko", slow=False)
    tts.save(temp_tts)

    # ffmpeg로 보컬 사운드에 리버브와 피치 튜닝 적용하여 몽환적인 보컬 이펙트 생성
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_tts,
        "-af", "asetrate=44100*1.08,atempo=0.92,aecho=0.8:0.7:40:0.25,volume=1.2",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_standalone_studio_track(style_tags: str, lyrics_text: str, output_path: str):
    """
    Suno API가 없는 로컬/액션 실행 시,
    기존 3대 명곡 오케스트라 사운드스케이프에 멜로딕 보컬 하모니와 현대적인 리마스터링을 결합하여
    완성도 높은 음원을 제작합니다.
    """
    music_dir = "assets/audio/music"
    tracks = glob.glob(f"{music_dir}/*.mp3") + glob.glob(f"{music_dir}/*.wav")
    chosen_bgm = random.choice(tracks) if tracks else None

    if not chosen_bgm:
        raise FileNotFoundError(f"{music_dir} 에 배경 음원이 없습니다.")

    bgm_audio = AudioSegment.from_file(chosen_bgm)
    # 2분 내외로 컷
    bgm_audio = bgm_audio[:130000].fade_out(4000)

    # 보컬 트랙 생성
    vocal_mp3 = "temp/vocal_fallback.mp3"
    create_fallback_vocal_track(lyrics_text, vocal_mp3)
    vocal_audio = AudioSegment.from_file(vocal_mp3)

    # 보컬을 BGM 인트로 10초 후에 자연스럽게 믹싱
    mixed = bgm_audio.overlay(vocal_audio + 2, position=8000)
    # 후반부 코러스에 한 번 더 레이어링
    if len(bgm_audio) > 60000:
        mixed = mixed.overlay(vocal_audio, position=50000)

    temp_mix_wav = "temp/mix_temp.wav"
    mixed.normalize(headroom=0.8).export(temp_mix_wav, format="wav")

    # 스튜디오 마스터링 DSP 체인 (서브베이스 강화 + 트레블 에어 + 리미터)
    mastering_dsp = "bass=g=2.5:f=80,equalizer=f=3200:t=q:w=1.2:g=2.0,treble=g=1.5:f=6000,stereotools=mlev=1.15,alimiter=limit=0.92:attack=5:release=50"
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_mix_wav,
        "-af", mastering_dsp,
        "-b:a", "320k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[Studio Engine] 폴백 스튜디오 마스터링 완료: {output_path}")
