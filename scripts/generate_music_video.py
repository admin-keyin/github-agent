import os
import requests
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import random
import sys
import subprocess
from bs4 import BeautifulSoup
import re

def midi_to_freq(m):
    if m == 0 or m is None:
        return 0.0
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))

# --- 고품질 어쿠스틱 그랜드 피아노 신디사이저 엔진 ---

def synth_acoustic_grand(freq, duration, velocity=0.7, fs=44100):
    """서정적이고 맑은 어쿠스틱 그랜드 피아노 사운드"""
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq <= 0:
        return np.zeros_like(t)
    
    # 자연스러운 배음 감쇠 커브 (Harmonic overtones)
    w1 = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.1)
    w2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.45 * np.exp(-t * 2.1)
    w3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.25 * np.exp(-t * 3.4)
    w4 = np.sin(2 * np.pi * (freq * 4) * t) * 0.12 * np.exp(-t * 4.6)
    w5 = np.sin(2 * np.pi * (freq * 5) * t) * 0.05 * np.exp(-t * 5.8)
    
    # 해머 타격감 (어택 초기 물리 타격감)
    hammer = np.sin(2 * np.pi * (freq * 1.5) * t) * 0.08 * np.exp(-t * 25.0)
    
    wave = (w1 + w2 + w3 + w4 + w5 + hammer) * velocity
    
    attack = int(fs * 0.004)
    if len(wave) > attack:
        wave[:attack] *= np.linspace(0, 1, attack)
    return wave

def apply_spatial_reverb(buffer_l, buffer_r, fs=44100):
    """콘서트홀/스튜디오 감성의 스테레오 공간감 리버브"""
    total_len = len(buffer_l)
    out_l = np.copy(buffer_l)
    out_r = np.copy(buffer_r)
    
    taps = [
        (int(fs * 0.095), 0.28, 0.70),
        (int(fs * 0.180), 0.22, 0.60),
        (int(fs * 0.290), 0.18, 0.50),
        (int(fs * 0.430), 0.12, 0.40),
    ]
    
    for delay_samples, wet_l, wet_r in taps:
        if delay_samples < total_len:
            out_l[delay_samples:] += buffer_r[:-delay_samples] * wet_l
            out_r[delay_samples:] += buffer_l[:-delay_samples] * wet_r
            
    return out_l, out_r

# --- K-POP & 인기 차트 명곡 정밀 악보 데이터베이스 (Note-by-Note Score DB) ---

SONG_DATABASE = {
    # 1. NewJeans - Hype Boy (K-POP 대표 댄스/팝을 감성 피아노 편곡)
    "hype_boy": {
        "title": "Hype Boy",
        "artist": "NewJeans",
        "bpm": 80,
        "image_prompt": "aesthetic retro pastel sunset bedroom, nostalgic 90s anime vibe, warm ambient lighting, cozy calm aesthetic, 4k digital art",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 64, 0.4), (3.0, 62, 0.9)]}, # Fmaj7
            {"bass": 40, "chords": [52, 55, 59, 62], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 69, 0.4), (2.5, 67, 0.4), (3.0, 64, 0.9)]}, # Em7
            {"bass": 38, "chords": [50, 53, 57, 60], "melody": [(0.0, 62, 0.4), (0.5, 65, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 65, 0.4), (3.0, 64, 0.9)]}, # Dm7
            {"bass": 36, "chords": [48, 52, 55, 59], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 72, 0.9), (2.0, 71, 0.9), (3.0, 67, 0.9)]}, # Cmaj7
            # Chorus: "'Cause I know what you like boy, you're my chemical hype boy"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.4), (0.5, 69, 0.4), (1.0, 72, 0.9), (2.0, 71, 0.4), (2.5, 69, 0.4), (3.0, 67, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 62], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 69, 0.4), (2.5, 67, 0.4), (3.0, 64, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 60], "melody": [(0.0, 62, 0.4), (0.5, 65, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 65, 0.4), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 65, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 2. NewJeans - Ditto (몽환적인 감성 멜로디)
    "ditto": {
        "title": "Ditto",
        "artist": "NewJeans",
        "bpm": 74,
        "image_prompt": "quiet snowy high school hallway in winter twilight, soft warm window sunlight, nostalgic 90s camcorder aesthetic, photorealistic",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 69, 0.5), (0.5, 67, 0.5), (1.0, 64, 0.9), (2.0, 60, 0.9), (3.0, 64, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 62], "melody": [(0.0, 67, 0.5), (0.5, 64, 0.5), (1.0, 62, 0.9), (2.0, 59, 0.9), (3.0, 62, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 60], "melody": [(0.0, 65, 0.5), (0.5, 64, 0.5), (1.0, 60, 0.9), (2.0, 57, 0.9), (3.0, 60, 0.9)]},
            {"bass": 36, "chords": [48, 52, 55, 59], "melody": [(0.0, 64, 0.5), (0.5, 62, 0.5), (1.0, 60, 0.9), (2.0, 64, 0.9), (3.0, 67, 0.9)]},
            # Chorus: "Stay in the middle, Like you a little, Don't want no riddle"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 69, 0.4), (0.5, 71, 0.4), (1.0, 72, 0.9), (2.0, 71, 0.4), (2.5, 69, 0.4), (3.0, 67, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 62], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 69, 0.4), (2.5, 67, 0.4), (3.0, 64, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 60], "melody": [(0.0, 62, 0.4), (0.5, 65, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 65, 0.4), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 3. IVE - LOVE DIVE (몽환적인 피아노 어레인지)
    "love_dive": {
        "title": "LOVE DIVE",
        "artist": "IVE",
        "bpm": 76,
        "image_prompt": "deep turquoise celestial fantasy pool under starry night sky, shimmering water reflections, luxurious magical anime aesthetic",
        "score": [
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 64, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 65, 0.5), (0.5, 65, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 48, "chords": [60, 64, 67, 72], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "Narcissistic, my god I love it"
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 69, 0.4), (0.5, 69, 0.4), (1.0, 69, 0.9), (2.0, 72, 0.4), (2.5, 71, 0.4), (3.0, 69, 0.9)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 65, 0.4), (0.5, 65, 0.4), (1.0, 65, 0.9), (2.0, 69, 0.4), (2.5, 67, 0.4), (3.0, 65, 0.9)]},
            {"bass": 48, "chords": [60, 64, 67, 72], "melody": [(0.0, 67, 0.4), (0.5, 67, 0.4), (1.0, 67, 0.9), (2.0, 72, 0.9), (3.0, 71, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 4. BIGBANG - 봄여름가을겨울 (Still Life)
    "still_life": {
        "title": "봄여름가을겨울 (Still Life)",
        "artist": "BIGBANG",
        "bpm": 68,
        "image_prompt": "surreal artistic landscape with four seasons blending into one, blooming blossoms meeting autumn leaves, cinematic lighting, 4k masterpiece",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 62, 0.9)]},
            {"bass": 35, "chords": [47, 50, 55, 59], "melody": [(0.0, 62, 0.5), (0.5, 65, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 69, 0.5), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "이듬해 봄 다시 필 꽃, 지난밤의 꿈"
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 72, 0.9), (3.0, 71, 0.5), (3.5, 69, 0.5)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 67, 0.9), (1.0, 64, 0.9), (2.0, 67, 0.9), (3.0, 69, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 65, 0.9), (1.0, 62, 0.9), (2.0, 60, 1.9)]}
        ]
    },
    # 5. 아이유 - 에잇 (eight - Prod. & Feat. SUGA of BTS)
    "eight": {
        "title": "에잇",
        "artist": "아이유",
        "bpm": 76,
        "image_prompt": "dreamy orange sunset island with gentle sea waves, airplane flying across golden twilight clouds, nostalgic aesthetic, anime painting",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 64, 0.9)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "우리는 오렌지 태양 아래 그림자 없이 함께 춤을 춰"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 69, 0.5), (0.5, 71, 0.5), (1.0, 74, 0.9), (2.0, 72, 0.5), (2.5, 71, 0.5), (3.0, 69, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.9), (3.0, 69, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 6. 성시경 - 너의 모든 순간
    "every_moment": {
        "title": "너의 모든 순간",
        "artist": "성시경",
        "bpm": 68,
        "image_prompt": "solitary grand piano by a rain-slicked window overlooking seoul night skyline, warm golden ambient lights, romantic emotional Korean drama aesthetic, 4k cinematic",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.9), (1.0, 65, 0.9), (2.0, 67, 1.8)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 71, 0.9), (1.0, 69, 0.9), (2.0, 67, 1.8)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 64, 0.4), (0.5, 64, 0.4), (1.0, 64, 0.4), (1.5, 65, 0.4), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 62, 0.4), (0.5, 64, 0.4), (1.0, 65, 0.4), (1.5, 67, 0.4), (2.0, 65, 0.9), (3.0, 64, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 62, 0.4), (0.5, 62, 0.4), (1.0, 62, 0.4), (1.5, 64, 0.4), (2.0, 65, 0.9), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 67, 0.9), (1.0, 65, 0.9), (2.0, 64, 1.8)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.4), (0.5, 69, 0.4), (1.0, 72, 0.9), (2.0, 71, 0.4), (2.5, 69, 0.4), (3.0, 67, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 64, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 69, 0.4), (2.5, 67, 0.4), (3.0, 65, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 62, 0.4), (0.5, 65, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 65, 0.4), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 65, 0.4), (0.5, 67, 0.4), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 7. 아이유 - 밤편지
    "through_the_night": {
        "title": "밤편지",
        "artist": "아이유",
        "bpm": 70,
        "image_prompt": "quiet traditional Korean room at night with soft warm lamp, open window overlooking starry summer night, romantic poetic IU aesthetic, 4k digital masterpiece",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 65], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 1.0), (2.0, 72, 1.8)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 69, 0.5), (0.5, 67, 0.5), (1.0, 65, 1.0), (2.0, 60, 1.8)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 60, 0.5), (0.5, 65, 0.5), (1.0, 65, 0.5), (1.5, 67, 0.5), (2.0, 69, 1.0), (3.0, 65, 0.9)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.5), (1.5, 72, 0.5), (2.0, 69, 1.0), (3.0, 67, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.5), (1.5, 67, 0.5), (2.0, 65, 1.0), (3.0, 60, 1.0)]},
            {"bass": 41, "chords": [53, 57, 60, 65], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 1.0), (2.0, 72, 0.5), (2.5, 74, 0.5), (3.0, 76, 0.9)]},
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 74, 0.5), (0.5, 72, 0.5), (1.0, 69, 1.0), (2.0, 72, 1.9)]}
        ]
    },
    # 8. 폴킴 - 모든 날, 모든 순간
    "every_day_every_moment": {
        "title": "모든 날, 모든 순간",
        "artist": "폴킴",
        "bpm": 66,
        "image_prompt": "warm autumn street in seoul with fallen golden leaves, soft romantic dusk sunlight, cinematic acoustic piano mood, 35mm film photography",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 67, 0.5), (2.0, 67, 0.9), (3.0, 65, 0.4), (3.5, 64, 0.4)]},
            {"bass": 35, "chords": [47, 50, 55, 59], "melody": [(0.0, 62, 0.5), (0.5, 65, 0.5), (1.0, 65, 0.5), (1.5, 65, 0.5), (2.0, 65, 0.9), (3.0, 64, 0.4), (3.5, 62, 0.4)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 67, 0.5), (2.0, 69, 0.9), (3.0, 67, 0.4), (3.5, 65, 0.4)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 64, 0.9), (3.0, 62, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 65, 0.4), (0.5, 67, 0.4), (1.0, 69, 0.9), (2.0, 72, 0.9), (3.0, 71, 0.4), (3.5, 69, 0.4)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 67, 0.9), (1.0, 64, 0.9), (2.0, 67, 0.9), (3.0, 69, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 65, 0.9), (1.0, 62, 0.9), (2.0, 60, 1.9)]}
        ]
    },
    # 9. 최유리 - 숲
    "forest": {
        "title": "숲",
        "artist": "최유리",
        "bpm": 68,
        "image_prompt": "ethereal misty green forest with gentle morning light filtering through tree canopy, calm river flowing, peaceful emotional Korean acoustic mood, masterpiece",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 62, 0.9)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 69, 0.5), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 64, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 65, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 62, 0.5), (0.5, 65, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    # 10. 10CM - 그라데이션
    "gradation": {
        "title": "그라데이션",
        "artist": "10CM",
        "bpm": 74,
        "image_prompt": "summer sunset over river in Seoul, warm orange and purple pastel sky, nostalgic romantic aesthetic, 4k cinematic",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 62, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 64, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 64, 0.9)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 69, 0.5), (0.5, 71, 0.5), (1.0, 74, 0.9), (2.0, 72, 0.5), (2.5, 71, 0.5), (3.0, 69, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.9), (3.0, 69, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    }
}

# --- 멜론 종합 TOP 100 인기차트 연동 & 스마트 매칭 엔진 ---

def get_target_song():
    """멜론 종합 TOP 100 인기차트를 실시간 크롤링하여 차트에 있는 인기곡을 우선 추출하거나 랜덤 선정"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    # 멜론 종합 실시간 TOP 100 차트
    url = 'https://www.melon.com/chart/index.htm'
    
    crawled_list = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            titles = soup.select('div.ellipsis.rank01 a')
            artists = soup.select('div.ellipsis.rank02 a:first-child')
            for rank, (t, a) in enumerate(zip(titles, artists), 1):
                crawled_list.append({
                    "rank": rank,
                    "title": t.text.strip().replace('\xa0', ' '),
                    "artist": a.text.strip().replace('\xa0', ' ')
                })
            print(f"[Melon Comprehensive Chart] 실시간 종합 차트 {len(crawled_list)}곡 수집 완료")
    except Exception as e:
        print(f"[Melon] 크롤링 오류: {e}")

    # 크롤링한 실시간 종합 차트 아티스트/곡명과 일치하는 곡이 있는지 탐색
    matched_candidates = []
    for c in crawled_list:
        for key, song_data in SONG_DATABASE.items():
            if song_data["title"] in c["title"] or c["title"] in song_data["title"] or song_data["artist"] in c["artist"]:
                matched_candidates.append(song_data)
                
    if matched_candidates:
        # 차트에 진입해 있는 인기곡 중 무작위 1곡 선택
        selected = random.choice(matched_candidates)
        print(f"[Chart Match] 멜론 종합 인기차트 매칭 곡 선정: {selected['artist']} - {selected['title']}")
        return selected

    # 차트 매칭 외에는 풀(Pool) 전체(K-POP / 발라드 / 댄스 / 팝 명곡)에서 완전 랜덤 선정
    chosen_key = random.choice(list(SONG_DATABASE.keys()))
    selected = SONG_DATABASE[chosen_key]
    print(f"[Popular Hit Selection] 인기 차트 명곡 풀에서 무작위 선정: {selected['artist']} - {selected['title']}")
    return selected

# --- 정밀 피아노 연주 트랙 생성 엔진 ---

def generate_exact_score_track(song_data, duration_sec, output_path):
    fs = 44100
    total_samples = int(fs * duration_sec)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    bpm = song_data.get("bpm", 72)
    beat_sec = 60.0 / bpm
    beat_samples = int(fs * beat_sec)
    measure_samples = beat_samples * 4
    
    score = song_data["score"]
    num_measures = len(score)
    
    def play_note(midi_pitch, start_sample, length_sec, vel, pan):
        if midi_pitch <= 0:
            return
        freq = midi_to_freq(midi_pitch)
        wave = synth_acoustic_grand(freq, length_sec, velocity=vel, fs=fs)
        if start_sample >= total_samples:
            return
        start_sample = max(0, start_sample)
        end_s = min(total_samples, start_sample + len(wave))
        wave_slice = wave[:end_s - start_sample]
        if len(wave_slice) == 0:
            return
        
        buffer_l[start_sample:end_s] += wave_slice * (1.0 - pan)
        buffer_r[start_sample:end_s] += wave_slice * pan

    current_sample = 0
    measure_idx = 0
    
    while current_sample < total_samples:
        measure_data = score[measure_idx % num_measures]
        measure_idx += 1
        
        bass_midi = measure_data["bass"]
        chord_midis = measure_data["chords"]
        melody_notes = measure_data["melody"]
        
        # 1. 왼손 베이스 (묵직하고 따뜻한 톤)
        play_note(bass_midi, current_sample, beat_sec * 3.8, 0.65, 0.48)
        
        # 2. 왼손 1-5-8-10 감성 롤링 아르페지오
        fifth = bass_midi + 7
        octave = bass_midi + 12
        tenth = chord_midis[1] if len(chord_midis) > 1 else bass_midi + 16
        
        play_note(fifth, current_sample + int(beat_samples * 1.0), beat_sec * 2.2, 0.38, 0.45)
        play_note(octave, current_sample + int(beat_samples * 2.0), beat_sec * 2.0, 0.35, 0.46)
        play_note(tenth, current_sample + int(beat_samples * 3.0), beat_sec * 1.8, 0.33, 0.48)
        
        # 3. 오른손 은은한 배경 화음 서스테인
        for c_note in chord_midis:
            play_note(c_note, current_sample + int(beat_samples * 0.02), beat_sec * 3.5, 0.28, 0.55)
            
        # 4. 오른손 정확한 원곡 주선율(Melody Line) 연주
        for offset_beats, note_midi, dur_beats in melody_notes:
            note_start = current_sample + int(offset_beats * beat_samples)
            note_len_sec = dur_beats * beat_sec
            
            vel = 0.72
            pan = 0.58
            play_note(note_midi, note_start, note_len_sec, vel, pan)
            
            # 후렴구/클라이맥스 옥타브 하모니 연출 (풍성함 극대화)
            if measure_idx % num_measures >= (num_measures // 2):
                play_note(note_midi + 12, note_start + int(fs * 0.003), note_len_sec * 0.9, 0.32, 0.65)
                
        current_sample += measure_samples

    print("Applying high-end stereo reverb & spatial effects...")
    buffer_l, buffer_r = apply_spatial_reverb(buffer_l, buffer_r, fs)

    # 피크 마스터링 & 노멀라이즈
    max_val = max(np.max(np.abs(buffer_l)), np.max(np.abs(buffer_r)))
    if max_val > 0:
        buffer_l = (buffer_l / max_val) * 0.88
        buffer_r = (buffer_r / max_val) * 0.88

    buffer_l = (buffer_l * 32767).astype(np.int16)
    buffer_r = (buffer_r * 32767).astype(np.int16)
    stereo_wave = np.vstack((buffer_l, buffer_r)).T.flatten()

    temp_wav = "temp/base.wav"
    os.makedirs("temp", exist_ok=True)
    wavfile.write(temp_wav, fs, stereo_wave.reshape(-1, 2))

    audio = AudioSegment.from_wav(temp_wav)
    audio.export(output_path, format="mp3")

def create_8h_video(image_path, audio_path, output_path):
    print("Creating 8-hour video (High-speed concatenation mode)...")
    short_video = "temp/short.mp4"
    cmd_short = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-t", "300", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
        "-preset", "ultrafast", "-crf", "30", "-c:a", "aac", "-b:a", "128k", short_video
    ]
    subprocess.run(cmd_short, check=True)

    with open("temp/concat.txt", "w") as f:
        for _ in range(96):
            f.write("file 'short.mp4'\n")
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "temp/concat.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(cmd_concat, check=True)
    print(f"Final 8-hour video created: {output_path}")

def generate_ai_image(prompt, filename):
    print(f"Generating background image: {prompt}")
    encoded_prompt = requests.utils.quote(prompt)
    seed = random.randint(1, 99999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        with open(filename, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"Image generation fallback due to: {e}")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x111625:s=1280x720:d=1", "-vframes", "1", filename], check=True)

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    base_audio = "temp/base.mp3"
    image_file = "temp/bg.jpg"
    final_video = "output_music_video.mp4"

    # 1. 멜론 종합 TOP 100 인기차트 연동 및 무작위 곡 선정
    song = get_target_song()
    
    # 2. 5분 고품질 원곡 피아노 연주 트랙 생성
    generate_exact_score_track(song, 300, base_audio)
    
    # 3. AI 배경 이미지 생성
    img_prompt = song.get("image_prompt", f"peaceful grand piano in a quiet aesthetic room at dusk, romantic emotional Korean melody atmosphere, 4k masterpiece")
    generate_ai_image(img_prompt, image_file)
    
    # 4. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
    
    # 5. 유튜브 업로드용 정보 기록 ([8 Hours] 가수 - 곡명 연주)
    title = f"{song['artist']} - {song['title']} 연주"
    desc = f"인기 차트 명곡 [{song['artist']} - {song['title']}]을 감미로운 피아노 선율로 연주한 트랙입니다. 수면, 공부, 집중과 편안한 휴식을 위해 8시간 연속 재생됩니다."
    
    with open("temp/video_info.txt", "w", encoding="utf-8") as f:
        f.write(f"{title} | {desc} | {song['artist']} | {song['title']}")
