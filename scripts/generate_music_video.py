import os
import sys
import glob
import random
import subprocess
import json
import time
import requests
import unicodedata
from pathlib import Path
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. 3대 지정 음원 목록 (이 3개 이외에는 절대 사용하지 않음) ---
ALLOWED_TRACKS = ["뇌룡격파", "용전", "화룡진군"]

# --- 2. 다양한 연주 스타일 (EDM / 댄스 / 클래식 / 피아노 / 리코더 / 기타 / 일렉 / 에픽) 마스터 설정 ---

PERFORMANCE_STYLES = {
    "edm": {
        "style_name": "EDM 페스티벌 리믹스",
        "title_template": "[Inkey EDM] 전략게임할 때 듣기 좋은 신나는 비트 - {name} (Festival EDM Drop)",
        "eq_colors": "0x00ffcc@0.95|0x00ff66@0.6", # 네온 사이안 & 일렉트릭 라임
        "title_color": (200, 255, 240, 255),
        "box_color": (0, 15, 12, 185),
        # 1.08배속 댄스 템포 업 + 강렬한 60Hz 펀치 킥 + 쏘우 신스 고음역 부스트 + 짧은 댄스 룸 에코
        "dsp_filter": "atempo=1.08,volume=-1.5dB,bass=g=4.5:f=65,equalizer=f=1200:t=q:w=1.0:g=2.5,treble=g=3.5:f=5000,aecho=0.8:0.75:15:0.12,stereotools=mlev=1.2,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "dance": {
        "style_name": "신나는 댄스 비트 리믹스",
        "title_template": "[Inkey 댄스] 가슴이 벅차오르는 신나는 댄스 비트 - {name} (Dance Remix)",
        "eq_colors": "0xff007f@0.95|0x9900ff@0.6", # 핫핑크 & 네온 퍼플
        "title_color": (255, 220, 245, 255),
        "box_color": (15, 5, 20, 185),
        # 1.05배속 경쾌한 그루브 + 탄탄한 110Hz 베이스 + 화려한 클럽 앰비언스
        "dsp_filter": "atempo=1.05,volume=-1.5dB,bass=g=3.8:f=110,equalizer=f=3500:t=q:w=1.2:g=3.0,aecho=0.8:0.8:20:0.15,stereotools=mlev=1.2,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "classic": {
        "style_name": "클래식 대심포니 오케스트라",
        "title_template": "[Inkey 클래식] 마음이 벅차오르는 대서사시 심포니 - {name} (Symphony Orchestra)",
        "eq_colors": "0xffdf80@0.95|0xd4af37@0.6", # 품격 있는 샴페인 골드
        "title_color": (255, 245, 210, 255),
        "box_color": (15, 12, 5, 180),
        # 묵직한 콘트라베이스/튜바(75Hz) + 풍부한 그랜드 콘서트홀 대향연 리버브 + 와이드 스테이지
        "dsp_filter": "volume=-1.5dB,bass=g=3.8:f=75,equalizer=f=1800:t=q:w=1.5:g=2.2,aecho=0.85:0.88:45:0.28,stereotools=mlev=1.25,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "piano": {
        "style_name": "감성 어쿠스틱 피아노 독주",
        "title_template": "[Inkey 피아노] 전략게임할 때 듣기 좋은 감성 피아노 선율 - {name} (Piano Solo)",
        "eq_colors": "white@0.95|0xddddff@0.5", # 순백 & 소프트 아이스 블루
        "title_color": (255, 255, 255, 255),
        "box_color": (5, 8, 15, 175),
        # 피아노 건반의 맑고 영롱한 고음 배음(3.8kHz 부스트) + 포근한 콘서트홀 잔향
        "dsp_filter": "volume=-1.5dB,highpass=f=40,equalizer=f=3800:t=q:w=1.2:g=3.5,treble=g=2.5:f=5500,aecho=0.8:0.86:38:0.25,stereotools=mlev=1.15,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1552422535-c45813c61732?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "recorder": {
        "style_name": "동화 감성 리코더 & 목관 합주",
        "title_template": "[Inkey 리코더] 마음이 벅차오르는 동화 감성 멜로디 - {name} (Woodwind Ver.)",
        "eq_colors": "0x7fffd4@0.95|0xffff99@0.6", # 파스텔 민트 & 옐로우
        "title_color": (230, 255, 245, 255),
        "box_color": (5, 20, 15, 175),
        # 맑고 순수한 리코더/목관 멜로디 대역(2.2kHz) 집중 부스트 + 따뜻한 룸 리버브
        "dsp_filter": "volume=-1.5dB,highpass=f=200,equalizer=f=2200:t=q:w=1.5:g=4.2,equalizer=f=900:t=q:w=1.2:g=2.5,aecho=0.8:0.8:28:0.2,stereotools=mlev=1.15,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "guitar": {
        "style_name": "어쿠스틱 & 나일론 기타 연주",
        "title_template": "[Inkey 어쿠스틱 기타] 심장을 울리는 감성 기타 선율 - {name} (Acoustic Guitar)",
        "eq_colors": "0xffaa33@0.95|0xcc6600@0.6", # 따뜻한 앰버 우드 & 골드
        "title_color": (255, 235, 205, 255),
        "box_color": (20, 12, 5, 180),
        # 통기타 바디 온기(150Hz) + 핑거링/스트럼 어택감(2.8kHz) + 어쿠스틱 스튜디오 잔향
        "dsp_filter": "volume=-1.5dB,bass=g=2.2:f=150,equalizer=f=2800:t=q:w=1.2:g=3.2,treble=g=2.8:f=5500,aecho=0.8:0.83:30:0.22,stereotools=mlev=1.18,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1525201548942-d8732f6617a0?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "electric": {
        "style_name": "강렬한 일렉 기타 & 락 밴드",
        "title_template": "[Inkey 일렉 기타] 심장을 뛰게 하는 강렬한 일렉트릭 연주 - {name} (Rock Electric Ver.)",
        "eq_colors": "0xff0033@0.95|0x9900ff@0.6", # 크림슨 레드 & 네온 퍼플
        "title_color": (255, 210, 220, 255),
        "box_color": (20, 5, 10, 185),
        # 질주하는 일렉기타 리프(4.2kHz) + 펀치감 넘치는 락 베이스 드라이브 + 파워풀 앰프 스테이지
        "dsp_filter": "volume=-1.5dB,bass=g=3.5:f=100,equalizer=f=1400:t=q:w=1.0:g=3.0,equalizer=f=4200:t=q:w=1.0:g=3.8,treble=g=2.5:f=6500,aecho=0.8:0.78:22:0.18,stereotools=mlev=1.2,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    },
    "epic": {
        "style_name": "웅장한 오리엔탈 판타지 라이브",
        "title_template": "[Inkey 연주] 전략게임할 때 듣기 좋은 웅장한 음악 - {name} (Live Orchestra Ver.)",
        "eq_colors": "0xff4500@0.95|0xffd700@0.7", # 타오르는 오렌지 골드
        "title_color": (255, 245, 210, 255),
        "box_color": (15, 8, 5, 180),
        # 브라스 & 타악기 타격감 + 풍부한 전장 라이브 잔향
        "dsp_filter": "volume=-1.5dB,bass=g=3.2:f=85,equalizer=f=3200:t=q:w=1.2:g=2.5,aecho=0.8:0.85:35:0.2,stereotools=mlev=1.2,alimiter=limit=0.95",
        "images": [
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1920&h=1080&q=90",
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1920&h=1080&q=90"
        ]
    }
}


# --- 3. 3대 원곡 기반 실시간 악기 합성 및 연주 엔진 (Real Instrument Timbre Synthesis) ---

import numpy as np
from scipy.signal import butter, lfilter, hilbert

def butter_bandpass_filter(data, lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = max(0.01, lowcut / nyq)
    high = min(0.99, highcut / nyq)
    if low >= high:
        low = high * 0.5
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)

def synthesize_instrument_melody(audio_segment, style_key):
    """
    원곡의 멜로디 및 피치/에너지를 실시간 분석하여
    피아노 / 리코더 / 어쿠스틱 기타 / 일렉 기타 / EDM 신스 & 드럼의
    실제 악기 물리 음색을 생성합니다.
    """
    samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2)).mean(axis=1)

    sr = audio_segment.frame_rate
    num_samples = len(samples)
    duration = num_samples / float(sr)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # 1. 멜로디 대역(200Hz ~ 3500Hz) 필터링 및 순시 주파수(피치) 추적
    try:
        melody_band = butter_bandpass_filter(samples, 250, 3200, sr, order=2)
        analytic_signal = hilbert(melody_band)
        amplitude_env = np.abs(analytic_signal)
        # 평활화
        window_size = int(sr * 0.02) # 20ms
        if window_size > 0:
            amplitude_env = np.convolve(amplitude_env, np.ones(window_size)/window_size, mode='same')
        
        # 순시 위상 및 주파수 추출
        instantaneous_phase = np.unwrap(np.angle(analytic_signal))
        instantaneous_freq = np.diff(instantaneous_phase) / (2.0 * np.pi) * sr
        instantaneous_freq = np.append(instantaneous_freq, instantaneous_freq[-1])
        instantaneous_freq = np.clip(instantaneous_freq, 150, 4000)
    except Exception as e:
        print(f"[Melody tracking fallback]: {e}")
        instantaneous_freq = np.full(num_samples, 440.0)
        amplitude_env = np.ones(num_samples)

    # 정규화된 앰플리튜드 엔벨로프
    max_env = np.max(amplitude_env) if np.max(amplitude_env) > 0 else 1.0
    norm_env = amplitude_env / max_env

    synth_audio = np.zeros(num_samples, dtype=np.float32)

    # 2. 각 악기별 고유 물리 파형 합성 (Timbre Synthesis)
    phase = np.cumsum(2.0 * np.pi * instantaneous_freq / sr)

    if style_key == "recorder":
        # 리코더/플루트: 순수 사인파 + 비브라토(5.5Hz) + 홀수 3차 배음 + 숨소리(Breath Noise) + Chiff 어택
        vibrato = 1.0 + 0.03 * np.sin(2.0 * np.pi * 5.5 * t)
        breath_noise = np.random.uniform(-0.06, 0.06, num_samples) * norm_env
        recorder_tone = (
            np.sin(phase * vibrato) * 0.75 +
            np.sin(phase * 3.0 * vibrato) * 0.20 +
            breath_noise
        )
        synth_audio = recorder_tone * np.power(norm_env, 0.8) * 1.5

    elif style_key == "piano":
        # 피아노: 해머 타건 어택 + 복합 배음 감쇠 (1f, 2f, 3f, 4f, 5f 배음) + 타건 노이즈
        piano_tone = (
            np.sin(phase) * 0.55 +
            np.sin(phase * 2.0) * 0.28 +
            np.sin(phase * 3.0) * 0.15 +
            np.sin(phase * 4.0) * 0.08 +
            np.sin(phase * 5.0) * 0.04
        )
        # 해머 타건 트랜지언트 시뮬레이션
        attack_env = np.clip(norm_env * 1.3, 0, 1.0)
        synth_audio = piano_tone * attack_env * 1.6

    elif style_key == "guitar":
        # 어쿠스틱 기타: Plucked String 풍부한 배음 + 브라이트한 핑거 스트럼 어택
        guitar_tone = (
            np.sin(phase) * 0.45 +
            np.sin(phase * 2.0) * 0.30 +
            np.sin(phase * 3.0) * 0.20 +
            np.sin(phase * 4.0) * 0.12 +
            np.sin(phase * 6.0) * 0.06
        )
        # 기타 바디 공명
        synth_audio = guitar_tone * np.power(norm_env, 0.9) * 1.5

    elif style_key == "electric":
        # 일렉 기타: 강력한 Sawtooth/Square 파형 + 진공관 오버드라이브 디스토션 (Tanh clipping) + 고출력 앰프 사운드
        saw_wave = 2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))
        distorted = np.tanh(saw_wave * 3.5 + np.sin(phase * 2.0) * 1.5)
        synth_audio = distorted * np.power(norm_env, 0.7) * 1.4

    elif style_key in ("edm", "dance"):
        # EDM / 댄스: 7-Oscillator SuperSaw 리드 + 4-on-the-floor 펀치 킥 드럼 & 하이햇 리듬 비트!
        saw1 = 2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))
        saw2 = 2.0 * ((phase * 1.008) / (2.0 * np.pi) - np.floor((phase * 1.008) / (2.0 * np.pi) + 0.5))
        saw3 = 2.0 * ((phase * 0.992) / (2.0 * np.pi) - np.floor((phase * 0.992) / (2.0 * np.pi) + 0.5))
        supersaw = (saw1 + saw2 + saw3) / 3.0
        lead_synth = supersaw * np.power(norm_env, 0.75)

        # 128BPM 4/4 펀치 킥 드럼 & 하이햇 합성
        bpm = 128.0
        beat_interval = 60.0 / bpm
        beat_times = t % beat_interval
        # 킥 드럼: 120Hz -> 45Hz 피치 스윕 펀치
        kick_env = np.exp(-beat_times * 18.0)
        kick_wave = np.sin(2.0 * np.pi * (50.0 + 90.0 * kick_env) * beat_times) * kick_env
        # 오픈 하이햇 (오프비트)
        hat_times = (t + beat_interval * 0.5) % beat_interval
        hat_env = np.exp(-hat_times * 35.0)
        hat_noise = np.random.uniform(-1.0, 1.0, num_samples) * hat_env * 0.25

        synth_audio = lead_synth * 1.2 + kick_wave * 0.8 + hat_noise * 0.4

    elif style_key == "classic":
        # 클래식 심포니: 비브라토 스트링 앙상블 + 브라스 하모닉스
        vibrato = 1.0 + 0.02 * np.sin(2.0 * np.pi * 5.0 * t)
        strings = (
            np.sin(phase * vibrato) * 0.5 +
            np.sin(phase * 2.0 * vibrato) * 0.3 +
            np.sin(phase * 3.0 * vibrato) * 0.15 +
            np.sin(phase * 4.0 * vibrato) * 0.1
        )
        synth_audio = strings * np.power(norm_env, 0.85) * 1.5

    else: # epic
        # 에픽 오케스트라 팡파르
        epic_tone = (
            np.sin(phase) * 0.6 +
            np.sin(phase * 2.0) * 0.35 +
            np.sin(phase * 3.0) * 0.2
        )
        synth_audio = epic_tone * np.power(norm_env, 0.8) * 1.4

    # 3. 신디사이즈된 악기 사운드를 AudioSegment로 변환
    synth_audio = np.clip(synth_audio, -1.0, 1.0)
    synth_int16 = (synth_audio * 32767).astype(np.int16)
    
    synth_seg = AudioSegment(
        synth_int16.tobytes(),
        frame_rate=sr,
        sample_width=2,
        channels=1
    ).set_channels(2)

    # 4. 원곡과 악기 솔로 멜로디의 절묘한 믹싱:
    # 원곡 볼륨을 살짝 낮춰서 배경(Backing)으로 깔고, 합성된 악기 멜로디를 전면에 강력하게 배치!
    backing_track = audio_segment - 5.0 # 원곡 반주화 (-5dB)
    lead_instrument = synth_seg + 3.0  # 솔로 악기 전면 부각 (+3dB)
    
    mixed_performance = backing_track.overlay(lead_instrument)
    return mixed_performance


def get_inkey_performance_track(selected_file=None, selected_style=None, output_mp3_path="temp/ai_song.mp3"):
    """
    지정된 3개 음원 중 하나를 선택하고, EDM/댄스/클래식/피아노/리코더/기타/일렉 등
    선택된 스타일에 맞추어 실제 악기 음색 합성(Timbre Synthesis)을 적용하여 연주합니다.
    """
    music_dir = "assets/audio/music"
    all_files = glob.glob(f"{music_dir}/*.mp3") + glob.glob(f"{music_dir}/*.wav")
    
    valid_files = []
    for f in all_files:
        stem = unicodedata.normalize('NFC', Path(f).stem)
        for allowed in ALLOWED_TRACKS:
            if allowed in stem:
                valid_files.append(f)
                break

    if not valid_files:
        raise FileNotFoundError(f"지정된 3개 음원({ALLOWED_TRACKS})을 {music_dir} 에서 찾을 수 없습니다.")

    chosen_file = None

    if selected_file and selected_file.strip() and selected_file.strip().lower() != "random":
        target = unicodedata.normalize('NFC', selected_file.strip())
        for f in valid_files:
            f_norm = unicodedata.normalize('NFC', f)
            f_base = unicodedata.normalize('NFC', os.path.basename(f))
            f_stem = unicodedata.normalize('NFC', Path(f).stem)
            if target in (f_norm, f_base, f_stem) or target in f_stem:
                chosen_file = f
                break
        if not chosen_file:
            print(f"[Notice] '{selected_file}' 대신 지정된 3개 음원 중 무작위 선택합니다.")

    if not chosen_file:
        chosen_file = random.choice(valid_files)

    song_name = unicodedata.normalize('NFC', Path(chosen_file).stem)

    # 연주 스타일 결정
    available_styles = list(PERFORMANCE_STYLES.keys())
    if selected_style and selected_style.strip().lower() in available_styles:
        style_key = selected_style.strip().lower()
    else:
        style_key = random.choice(available_styles)

    style_profile = PERFORMANCE_STYLES[style_key]

    print(f"\n=======================================================")
    print(f" [Inkey Studio Real-Instrument Synthesis Session]")
    print(f" [Original Track] {chosen_file}")
    print(f" [Song Name] {song_name}")
    print(f" [Performance Style] {style_profile['style_name']} ({style_key.upper()})")
    print(f"=======================================================")

    raw_audio = AudioSegment.from_file(chosen_file)
    original_duration = len(raw_audio) / 1000.0
    print(f"[원곡 길이] {original_duration:.1f}초 ({int(original_duration//60)}분 {int(original_duration%60)}초)")

    # 1. 실제 악기 음색 합성 및 멜로디 오버레이 생성
    print(f"[Synthesizing Timbre] '{style_profile['style_name']}' 실시간 악기 음색 물리 합성 중...")
    performed_audio = synthesize_instrument_melody(raw_audio, style_key)

    temp_synth_wav = "temp/synth_performed.wav"
    performed_audio.normalize(headroom=0.8).export(temp_synth_wav, format="wav")

    # 2. 선택된 스타일 전용 어쿠스틱 DSP 필터 체인 추가 적용
    dsp = style_profile["dsp_filter"]
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_synth_wav,
        "-af", dsp,
        "-ar", "44100",
        "-b:a", "320k",
        output_mp3_path
    ]
    subprocess.run(cmd, check=True)

    remastered_audio = AudioSegment.from_file(output_mp3_path)
    final_duration = len(remastered_audio) / 1000.0
    print(f"[Performance Complete] {output_mp3_path} (실제 악기 연주 완성, 재생 시간: {final_duration:.1f}초)")

    return song_name, chosen_file, final_duration, style_profile, style_key


# --- 4. Pillow 기반 감성/스타일별 타이틀 오버레이 생성기 ---

def create_title_overlay_png(title_text, style_profile, output_png_path, width=1280, height=720):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc"
    ]

    font = None
    for p in font_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 26)
                break
            except Exception:
                pass

    if not font:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (width - text_w) // 2
    y = 65
    pad_x = 24
    pad_y = 14

    # 반투명 라운드 박스
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
        radius=14,
        fill=style_profile["box_color"]
    )

    # 스타일 텍스트 컬러
    draw.text((x, y), title_text, font=font, fill=style_profile["title_color"])
    img.save(output_png_path, "PNG")


# --- 5. 고화질 배경 다운로드 & 비주얼라이저 비디오 합성 ---

def fetch_hd_background(style_profile, filename):
    chosen_url = random.choice(style_profile["images"])
    try:
        resp = requests.get(chosen_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            return
    except Exception as e:
        print(f"Image fetch fallback: {e}")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)


def create_equalizer_music_video(image_path, title_png_path, audio_path, style_profile, output_path):
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0

    eq_colors = style_profile["eq_colors"]
    filter_complex = (
        f"[0:v]scale=1280:720[bg];"
        f"[bg][1:v]overlay=0:0[bg_titled];"
        f"[2:a]showfreqs=s=880x140:mode=bar:fscale=log:colors={eq_colors}:win_size=1024[eq];"
        f"[bg_titled][eq]overlay=x=(W-w)/2:y=H-185[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", title_png_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[Visualizer Success] {output_path} (Duration: {duration_sec:.1f}s)")
    except Exception as e:
        print(f"Visualizer fallback simple render ({e})")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "320k", "-shortest", output_path
        ], check=True)


# --- 메인 실행 ---

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)

    input_music_file = os.getenv("INPUT_MUSIC_FILE", "").strip()
    input_style = os.getenv("INPUT_STYLE", os.getenv("INPUT_THEME", "")).strip().lower()
    custom_title = os.getenv("INPUT_CUSTOM_TITLE", "").strip()

    ai_mp3 = "temp/ai_song.mp3"
    bg_image = "temp/bg.jpg"
    title_png = "temp/title_overlay.png"
    final_video = "output_music_video.mp4"

    # 1. 원곡 선택 및 선택된 스타일(EDM/댄스/클래식/피아노/리코더/기타/일렉 등)로 연주 리마스터링
    song_name, chosen_path, duration, style_profile, style_key = get_inkey_performance_track(
        input_music_file, input_style, ai_mp3
    )

    # 2. 스타일별 맞춤 유튜브 영상 제목 생성
    if custom_title:
        final_title = custom_title
    else:
        final_title = style_profile["title_template"].format(name=song_name)

    print(f"\n[최종 비디오 제목] {final_title}")
    print(f"[스타일] {style_profile['style_name']}")

    # 3. 스타일별 감성 고화질 배경 이미지 준비
    fetch_hd_background(style_profile, bg_image)

    # 4. Pillow로 스타일 타이틀 PNG 오버레이 생성
    create_title_overlay_png(final_title, style_profile, title_png)

    # 5. 하이파이 이퀄라이저 비주얼라이저 비디오 렌더링
    create_equalizer_music_video(bg_image, title_png, ai_mp3, style_profile, final_video)

    # 6. 유튜브 업로드용 메타데이터 JSON 저장
    desc = (
        f"🎧 {final_title}\n\n"
        f"⚔️ 원곡명: {song_name}\n"
        f"🎼 연주 스타일: {style_profile['style_name']}\n"
        f"⏱️ 재생 시간: {int(duration // 60)}분 {int(duration % 60)}초\n"
        f"✨ 테마: 전략게임할 때 듣기 좋은 음악 / 마음이 벅차오르는 음악\n\n"
        f"Produced, Re-arranged & Performed by Inkey Music Studio.\n"
        f"3대 대표 명곡을 바탕으로 {style_profile['style_name']} 감성으로 재해석한 연주입니다.\n\n"
        f"#{song_name} #{style_key.upper()} #Inkey연주 #전략게임음악 #마음이벅차오르는음악 #게임BGM #InkeyMusic"
    )

    meta_info = {
        "title": final_title[:100],
        "description": desc,
        "artist": "Inkey Music Studio",
        "song_title": song_name
    }
    with open("temp/video_info.json", "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"\n[Video metadata saved successfully]: {final_title}")


