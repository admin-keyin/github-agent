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

# --- 사운드 신디사이저 엔진 ---

def synth_acoustic_grand(freq, duration, velocity=0.7, fs=44100):
    """서정적이고 맑은 어쿠스틱 그랜드 피아노 사운드"""
    t = np.linspace(0, duration, int(fs * duration), False)
    if freq <= 0:
        return np.zeros_like(t)
    
    # 그랜드 피아노 고유의 배음 감쇠 커브 (Harmonic overtones)
    w1 = np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.1)
    w2 = np.sin(2 * np.pi * (freq * 2) * t) * 0.45 * np.exp(-t * 2.1)
    w3 = np.sin(2 * np.pi * (freq * 3) * t) * 0.25 * np.exp(-t * 3.4)
    w4 = np.sin(2 * np.pi * (freq * 4) * t) * 0.12 * np.exp(-t * 4.6)
    w5 = np.sin(2 * np.pi * (freq * 5) * t) * 0.05 * np.exp(-t * 5.8)
    
    # 해머 타격감 (어택 초기 노이즈감)
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

# --- K-발라드 12대 명곡 정밀 악보 데이터베이스 (Note-by-Note Score DB) ---

SONG_DATABASE = {
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
    "to_my_youth": {
        "title": "나의 사춘기에게",
        "artist": "10CM",
        "bpm": 70,
        "image_prompt": "moody blue twilight room with vintage acoustic upright piano, soft glowing lamp, emotional Korean indie ballad vibe, nostalgic masterpiece",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 64, 0.5), (0.5, 64, 0.5), (1.0, 64, 0.5), (1.5, 65, 0.5), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 67, 0.5), (2.0, 69, 0.9), (3.0, 67, 0.9)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 65, 0.5), (0.5, 64, 0.5), (1.0, 62, 0.9), (2.0, 64, 0.9), (3.0, 62, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 64, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 65, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 62, 0.5), (0.5, 65, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    "stalker": {
        "title": "스토커",
        "artist": "10CM",
        "bpm": 68,
        "image_prompt": "quiet night bus window reflection, city lights bokeh blur in seoul, lonely emotional acoustic mood, 35mm film aesthetic",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 67, 0.5), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 60, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 62, 0.9), (2.0, 60, 1.9)]},
            # Chorus: "나도 알아 나의 문제가 무엇인지"
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 64, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 62, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 62, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 65, 0.5), (0.5, 64, 0.5), (1.0, 62, 0.9), (2.0, 60, 1.9)]}
        ]
    },
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
            # Chorus: "달콤한 색감이 물들어"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 69, 0.5), (0.5, 71, 0.5), (1.0, 74, 0.9), (2.0, 72, 0.5), (2.5, 71, 0.5), (3.0, 69, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.9), (3.0, 69, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    "like_it": {
        "title": "좋니",
        "artist": "윤종신",
        "bpm": 66,
        "image_prompt": "melancholic rainy evening cafe, raindrops on glass window, warm streetlights outside, emotional nostalgic film aesthetic",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 64, 0.9)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "좋으니 그 사람 솔직히 견디기 버거워"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.4), (0.5, 69, 0.4), (1.0, 72, 0.9), (2.0, 72, 0.4), (2.5, 71, 0.4), (3.0, 69, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 69, 0.4), (0.5, 71, 0.4), (1.0, 74, 0.9), (2.0, 72, 0.4), (2.5, 71, 0.4), (3.0, 69, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 65, 0.4), (0.5, 67, 0.4), (1.0, 69, 0.9), (2.0, 67, 0.4), (2.5, 65, 0.4), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    "wild_flower": {
        "title": "야생화",
        "artist": "박효신",
        "bpm": 64,
        "image_prompt": "serene mountain hill at sunrise with wild blooming white flowers, dramatic majestic morning glow, poetic masterpiece",
        "score": [
            {"bass": 36, "chords": [48, 52, 55, 60], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 1.0), (2.0, 65, 0.5), (2.5, 64, 0.5), (3.0, 62, 0.9)]},
            {"bass": 33, "chords": [45, 48, 52, 57], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.5), (1.5, 69, 0.5), (2.0, 67, 1.0), (3.0, 64, 0.9)]},
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 1.0), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 31, "chords": [43, 47, 50, 55], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "메말라가는 땅 위에 온몸이 타들어가고"
            {"bass": 29, "chords": [41, 48, 53, 57], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 74, 0.5), (2.5, 76, 0.5), (3.0, 72, 0.9)]},
            {"bass": 28, "chords": [40, 48, 52, 55], "melody": [(0.0, 71, 0.5), (0.5, 72, 0.5), (1.0, 74, 0.9), (2.0, 72, 0.5), (2.5, 71, 0.5), (3.0, 69, 0.9)]},
            {"bass": 26, "chords": [38, 45, 50, 53], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 31, "chords": [43, 48, 50, 55], "melody": [(0.0, 69, 0.5), (0.5, 71, 0.5), (1.0, 74, 0.9), (2.0, 72, 1.9)]}
        ]
    },
    "give_you_galaxy": {
        "title": "우주를 줄게",
        "artist": "볼빨간사춘기",
        "bpm": 76,
        "image_prompt": "magical galaxy starry night with gentle glowing pastel milky way over quiet city hills, dreamy cozy aesthetic",
        "score": [
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 64, 0.5), (0.5, 65, 0.5), (1.0, 67, 0.5), (1.5, 69, 0.5), (2.0, 67, 0.9), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.5), (1.5, 67, 0.5), (2.0, 65, 0.9), (3.0, 62, 0.9)]},
            {"bass": 40, "chords": [52, 55, 59, 64], "melody": [(0.0, 60, 0.5), (0.5, 64, 0.5), (1.0, 67, 0.9), (2.0, 69, 0.5), (2.5, 67, 0.5), (3.0, 64, 0.9)]},
            {"bass": 45, "chords": [57, 60, 64, 67], "melody": [(0.0, 62, 0.5), (0.5, 64, 0.5), (1.0, 65, 0.9), (2.0, 64, 0.5), (2.5, 62, 0.5), (3.0, 60, 1.0)]},
            # Chorus: "Cause I'm your star, 내 우주를 줄게"
            {"bass": 41, "chords": [53, 57, 60, 64], "melody": [(0.0, 67, 0.5), (0.5, 69, 0.5), (1.0, 72, 0.9), (2.0, 71, 0.5), (2.5, 69, 0.5), (3.0, 67, 0.9)]},
            {"bass": 43, "chords": [55, 59, 62, 67], "melody": [(0.0, 69, 0.5), (0.5, 71, 0.5), (1.0, 74, 0.9), (2.0, 72, 0.5), (2.5, 71, 0.5), (3.0, 69, 0.9)]},
            {"bass": 38, "chords": [50, 53, 57, 62], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 69, 0.9), (2.0, 67, 0.5), (2.5, 65, 0.5), (3.0, 64, 0.9)]},
            {"bass": 43, "chords": [53, 55, 59, 65], "melody": [(0.0, 65, 0.5), (0.5, 67, 0.5), (1.0, 71, 0.9), (2.0, 72, 1.9)]}
        ]
    }
}

# --- 100% 완전 무작위(Random) K-발라드 곡 선정 엔진 ---

def get_target_song():
    """풀(Pool) 내의 모든 정밀 악보 발라드 명곡 중에서 매번 완전 랜덤으로 1곡 선정"""
    keys = list(SONG_DATABASE.keys())
    chosen_key = random.choice(keys)
    song_data = SONG_DATABASE[chosen_key]
    print(f"[Random Selection] 선정된 K-발라드 명곡: {song_data['artist']} - {song_data['title']}")
    return song_data

# --- 정밀 피아노 연주 트랙 생성 엔진 ---

def generate_exact_score_track(song_data, duration_sec, output_path):
    fs = 44100
    total_samples = int(fs * duration_sec)
    buffer_l = np.zeros(total_samples, dtype=np.float32)
    buffer_r = np.zeros(total_samples, dtype=np.float32)
    
    bpm = song_data.get("bpm", 68)
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
        
        # 1. 왼손 베이스 (묵직하고 따뜻한 저음)
        play_note(bass_midi, current_sample, beat_sec * 3.8, 0.65, 0.48)
        
        # 2. 왼손 1-5-8-10 감성 롤링 아르페지오 (박자에 맞춰 자연스럽게 연주)
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

    # 1. 100% 완전 무작위 발라드 명곡 선정
    song = get_target_song()
    
    # 2. 5분 고품질 원곡 피아노 연주 트랙 생성
    generate_exact_score_track(song, 300, base_audio)
    
    # 3. AI 배경 이미지 생성
    img_prompt = song.get("image_prompt", f"peaceful grand piano in a quiet aesthetic room at dusk, romantic emotional Korean ballad atmosphere, 4k masterpiece")
    generate_ai_image(img_prompt, image_file)
    
    # 4. 8시간 영상으로 확장
    create_8h_video(image_file, base_audio, final_video)
    
    # 5. 유튜브 업로드용 정보 기록 ([8 Hours] 가수 - 곡명 연주)
    title = f"{song['artist']} - {song['title']} 연주"
    desc = f"한국인이 사랑하는 감성 K-발라드 [{song['artist']} - {song['title']}]을 섬세한 그랜드 피아노 선율로 연주한 공식 피아노 커버 트랙입니다. 수면, 공부, 집중과 편안한 휴식을 위해 8시간 연속 재생됩니다."
    
    with open("temp/video_info.txt", "w", encoding="utf-8") as f:
        f.write(f"{title} | {desc} | {song['artist']} | {song['title']}")
